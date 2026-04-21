#!/usr/bin/env python3
"""Minne 商品自動登録（requests版 - ブラウザ不要）"""

import os
import re
import json
import requests
from bs4 import BeautifulSoup

MINNE_EMAIL    = os.environ.get("MINNE_EMAIL", "")
MINNE_PASSWORD = os.environ.get("MINNE_PASSWORD", "")

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")


def _login(session: requests.Session, email: str, password: str, log=print) -> bool:
    """Minneにログインしてセッションを確立する。成功するとTrueを返す。"""
    # Step1: ログインページを取得してCSRFとクッキーを確保
    log("ログインページを取得中...")
    r = session.get(
        "https://minne.com/users/sign_in",
        headers={"Accept": "text/html,application/xhtml+xml,*/*", "Referer": "https://minne.com/"},
        timeout=20,
    )
    soup = BeautifulSoup(r.text, "html.parser")

    # フォーム内の全hidden inputを収集
    form = soup.find("form", action=re.compile(r"sign_in", re.I))
    if not form:
        form = soup.find("form")

    form_fields = {}
    if form:
        for inp in form.find_all("input"):
            name = inp.get("name", "")
            val  = inp.get("value", "")
            if name:
                form_fields[name] = val
    log(f"フォームフィールド: {list(form_fields.keys())}")

    # メタタグからCSRFを補完
    meta = soup.find("meta", {"name": "csrf-token"})
    if meta and meta.get("content"):
        form_fields["authenticity_token"] = meta["content"]

    # メールアドレスとパスワードをセット（Deviseの標準フィールド名）
    form_fields["user[email]"]    = email
    form_fields["user[password]"] = password
    # コミットボタン値
    form_fields.setdefault("commit", "ログイン")

    # Step2: フォームPOST
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
    log(f"ログイン後URL: {r2.url} (HTTP {r2.status_code})")

    # sign_inページに戻ってきたら失敗
    if "sign_in" in r2.url:
        # Step3: JSON API でリトライ
        log("フォームログイン失敗。JSON APIを試行中...")
        csrf = form_fields.get("authenticity_token", "")
        r3 = session.post(
            "https://minne.com/api/v2/sign_in",
            json={"email": email, "password": password},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf,
                "Origin": "https://minne.com",
                "Referer": "https://minne.com/users/sign_in",
            },
            timeout=30,
        )
        log(f"JSON API レスポンス: {r3.status_code}")
        if r3.status_code == 200:
            try:
                token = r3.json().get("token") or r3.json().get("access_token", "")
                if token:
                    session.headers["Authorization"] = f"Bearer {token}"
                    log("JWT認証成功")
                    return True
            except Exception:
                pass

        # Step4: /api/v1 でリトライ
        r4 = session.post(
            "https://minne.com/api/v1/auth/sign_in",
            json={"email": email, "password": password},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": "https://minne.com",
                "Referer": "https://minne.com/users/sign_in",
            },
            timeout=30,
        )
        log(f"API v1 レスポンス: {r4.status_code}")
        if r4.status_code == 200:
            try:
                token = r4.json().get("token") or r4.json().get("access_token", "")
                if token:
                    session.headers["Authorization"] = f"Bearer {token}"
                    return True
            except Exception:
                pass

        return False

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
            "・MinneはSNSログイン（Google/Apple/LINE）のみの場合、"
            "メール+パスワードでのログインができません"
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
