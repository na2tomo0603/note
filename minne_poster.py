#!/usr/bin/env python3
"""Minne 商品自動登録（requests版 - ブラウザ不要）"""

import os
import re
import requests
from bs4 import BeautifulSoup

MINNE_EMAIL    = os.environ.get("MINNE_EMAIL", "")
MINNE_PASSWORD = os.environ.get("MINNE_PASSWORD", "")

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")


def _login(session: requests.Session, email: str, password: str, log=print) -> bool:
    """Minneにログインしてセッションを確立する。成功するとTrueを返す。"""
    log("ログインページを取得中...")
    r = session.get(
        "https://minne.com/users/sign_in",
        headers={"Accept": "text/html,application/xhtml+xml,*/*", "Referer": "https://minne.com/"},
        timeout=20,
    )
    soup = BeautifulSoup(r.text, "html.parser")

    # ページタイトルでブロックを検出
    title_tag = soup.find("title")
    title = title_tag.get_text() if title_tag else ""
    log(f"ページタイトル: {title}")

    # フォーム内の全inputを収集
    form = soup.find("form", action=re.compile(r"sign_in", re.I))
    if not form:
        form = soup.find("form")

    form_fields = {}
    if form:
        action = form.get("action", "")
        log(f"フォームaction: {action}")
        for inp in form.find_all("input"):
            name = inp.get("name", "")
            val  = inp.get("value", "")
            if name:
                form_fields[name] = val
    else:
        log("警告: フォームが見つかりません（bot検知の可能性）")

    log(f"フォームフィールド: {list(form_fields.keys())}")

    # メタタグからCSRFを補完
    meta = soup.find("meta", {"name": "csrf-token"})
    if meta and meta.get("content"):
        form_fields["authenticity_token"] = meta["content"]
        log("CSRFトークン: 取得済み")
    else:
        log("警告: CSRFトークンが見つかりません")

    form_fields["user[email]"]    = email
    form_fields["user[password]"] = password
    form_fields.setdefault("commit", "ログイン")

    log("ログイン送信中...")
    r2 = session.post(
        "https://minne.com/users/sign_in",
        data=form_fields,
        headers={
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://minne.com/users/sign_in",
            "Origin": "https://minne.com",
        },
        allow_redirects=True,
        timeout=30,
    )
    log(f"ログイン後URL: {r2.url}")
    log(f"HTTPステータス: {r2.status_code}")

    # ページ内容でログイン結果を判定
    soup2 = BeautifulSoup(r2.text, "html.parser")
    title2_tag = soup2.find("title")
    title2 = title2_tag.get_text() if title2_tag else ""
    log(f"遷移後ページ: {title2}")

    # エラーメッセージを確認
    alert = soup2.find(class_=re.compile(r"alert|error|flash", re.I))
    if alert:
        log(f"ページエラー: {alert.get_text(strip=True)[:100]}")

    # 2段階認証ページかチェック
    page_text = r2.text.lower()
    if "two_factor" in r2.url or "otp" in r2.url or "二段階" in r2.text or "認証コード" in r2.text:
        log("→ 二段階認証ページに遷移しました")
        raise ValueError(
            "Minneの二段階認証が有効です。\n"
            "Minne設定 → セキュリティ → 二段階認証を一時的に無効にしてから再度お試しください。"
        )

    # sign_inページに戻ってきたら失敗
    if "sign_in" in r2.url:
        log("→ ログインページに戻りました（認証失敗）")
        return False

    # ログイン成功確認（マイページ等に遷移しているか）
    log("→ ログイン成功")
    return True


def _get_csrf(session: requests.Session, url: str) -> str:
    r = session.get(url, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    meta = soup.find("meta", {"name": "csrf-token"})
    if meta:
        return meta.get("content", "")
    inp = soup.find("input", {"name": "authenticity_token"})
    return inp["value"] if inp else ""


def post_product(product_dict: dict, image_paths: list, log=print, headless: bool = True) -> str:
    email    = MINNE_EMAIL    or product_dict.get("_minne_email", "")
    password = MINNE_PASSWORD or product_dict.get("_minne_password", "")

    if not email or not password:
        raise ValueError("Minneのメールアドレスとパスワードを設定してください")

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "ja,en;q=0.9"})

    log("Minneにログイン中...")
    ok = _login(session, email, password, log)
    if not ok:
        raise ValueError(
            "Minneログイン失敗。\n"
            "・メールアドレスとパスワードが正しいか確認してください\n"
            f"・入力メール: {email}\n"
            "・パスワードを忘れた場合はminne.comで再設定してください"
        )
    log("ログイン完了")

    # ── 商品登録ページのCSRF取得 ──
    log("商品登録ページを開いています...")
    csrf = _get_csrf(session, "https://minne.com/items/new")
    log(f"CSRF: {'取得済み' if csrf else 'なし'}")

    # ── 画像アップロード ──
    image_ids = []
    if image_paths:
        log(f"画像をアップロード中（{len(image_paths[:5])}枚）...")
        for path in image_paths[:5]:
            try:
                with open(path, "rb") as f:
                    files = {"item_image[image]": (os.path.basename(path), f, "image/jpeg")}
                    ur = session.post(
                        "https://minne.com/item_images",
                        files=files,
                        headers={"X-CSRF-Token": csrf, "X-Requested-With": "XMLHttpRequest"},
                        timeout=30,
                    )
                    data = ur.json()
                    if data.get("id"):
                        image_ids.append(str(data["id"]))
                        log(f"画像アップロード完了: {data['id']}")
            except Exception as e:
                log(f"画像アップロード失敗: {e}")

    # ── 商品データ送信 ──
    log("商品情報を送信中...")
    title       = product_dict.get("title", "")[:60]
    description = product_dict.get("description", "")[:1000]
    price       = product_dict.get("price", 0)
    stock       = product_dict.get("stock", 1)

    form_data = {
        "authenticity_token": csrf,
        "item[name]":         title,
        "item[description]":  description,
        "item[price]":        str(price),
        "item[quantity]":     str(stock),
        "item[status]":       "draft",
        "commit":             "下書き保存",
    }
    for img_id in image_ids:
        form_data["item[item_image_ids][]"] = img_id

    r = session.post(
        "https://minne.com/items",
        data=form_data,
        allow_redirects=True,
        timeout=30,
    )

    log(f"送信完了: {r.url}")
    if r.status_code in (200, 201, 302):
        log("Minne登録成功！")
        return r.url
    else:
        raise RuntimeError(f"登録失敗 (HTTP {r.status_code})")
