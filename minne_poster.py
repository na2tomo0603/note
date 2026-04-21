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

    # ── ログイン ──
    log("Minneにログイン中...")
    login_page = session.get("https://minne.com/users/sign_in", timeout=20)
    soup = BeautifulSoup(login_page.text, "html.parser")

    # フォームの全hidden inputを収集（CSRF・その他トークン）
    form = soup.find("form", action=lambda a: a and "sign_in" in a)
    if not form:
        form = soup.find("form")
    form_data = {}
    if form:
        for inp in form.find_all("input", {"type": ["hidden", "submit"]}):
            if inp.get("name"):
                form_data[inp["name"]] = inp.get("value", "")

    # ログイン情報を追加（フォームのname属性に合わせて両パターン試す）
    form_data.update({
        "user[email]": email,
        "user[password]": password,
        "email": email,
        "password": password,
    })
    log(f"フォーム送信中 (fields: {list(form_data.keys())})")

    r = session.post(
        "https://minne.com/users/sign_in",
        data=form_data,
        allow_redirects=True,
        timeout=30,
        headers={"Referer": "https://minne.com/users/sign_in",
                 "Origin": "https://minne.com"},
    )
    log(f"ログイン後URL: {r.url} (status: {r.status_code})")
    if "sign_in" in r.url or "login" in r.url.lower():
        raise ValueError(f"ログイン失敗：メールアドレスまたはパスワードを確認してください (URL: {r.url})")
    log(f"ログイン完了: {r.url}")

    # ── 商品登録ページのCSRF取得 ──
    log("商品登録ページを開いています...")
    csrf = _get_csrf(session, "https://minne.com/items/new")

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
    title = product_dict.get("title", "")[:60]
    description = product_dict.get("description", "")[:1000]
    price = product_dict.get("price", 0)
    stock = product_dict.get("stock", 1)

    form_data = {
        "authenticity_token": csrf,
        "item[name]": title,
        "item[description]": description,
        "item[price]": str(price),
        "item[quantity]": str(stock),
        "item[status]": "draft",
        "commit": "下書き保存",
    }
    for i, img_id in enumerate(image_ids):
        form_data[f"item[item_image_ids][]"] = img_id

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
