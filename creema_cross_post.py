#!/usr/bin/env python3
"""Creema商品を他のハンドメイドサイトにクロスポストするスクリプト"""
import sys
import os
import json
import re
import traceback
import urllib.request
from pathlib import Path

# ===== 認証情報設定 =====
# 環境変数 MINNE_EMAIL / MINNE_PASSWORD を設定するか、下記に直接入力してください
MINNE_EMAIL    = os.environ.get("MINNE_EMAIL", "na2ko0710@yahoo.co.jp")
MINNE_PASSWORD = os.environ.get("MINNE_PASSWORD", "na2tomo0603")

IICHI_EMAIL    = os.environ.get("IICHI_EMAIL", "your_iichi_email@example.com")
IICHI_PASSWORD = os.environ.get("IICHI_PASSWORD", "your_iichi_password")

IMAGES_DIR  = "creema_images"
OUTPUT_FILE = "creema_product.json"

SUPPORTED_SITES = ["minne", "iichi"]


# ---------- Creema スクレイピング ----------

def scrape_creema(page, url: str) -> dict:
    print(f"[Creema] 商品ページを取得中: {url}")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    title = _extract_text(page, [
        "h1.item-name",
        "h1[class*='ItemDetail'] span",
        "[class*='itemName']",
        "[class*='item-name']",
        "h1",
    ])

    price = _extract_text(page, [
        "[class*='itemPrice']",
        "[class*='item-price']",
        "[class*='price']",
        ".price",
    ])
    # 数字+円のみ残す
    price_clean = re.sub(r"[^\d]", "", price)

    description = _extract_text(page, [
        "[class*='itemDescription']",
        "[class*='item-description']",
        "[class*='description']",
        ".description",
    ])

    images = _extract_images(page, [
        "[class*='itemImage'] img",
        "[class*='item-image'] img",
        "[class*='gallery'] img",
        ".swiper-slide img",
        "[class*='slider'] img",
        "img[class*='item']",
    ])

    product = {
        "title":       title,
        "price":       price_clean,
        "description": description,
        "images":      images[:10],
        "source_url":  url,
    }
    print(f"[Creema] 取得完了 — タイトル: {title[:40]!r}  価格: {price_clean}円  画像: {len(images)}枚")
    return product


def _extract_text(page, selectors: list) -> str:
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                text = el.inner_text(timeout=2000).strip()
                if text:
                    return text
        except Exception:
            continue
    return ""


def _extract_images(page, selectors: list) -> list:
    seen = set()
    urls = []
    for sel in selectors:
        try:
            els = page.locator(sel).all()
            for el in els:
                src = el.get_attribute("src") or el.get_attribute("data-src") or ""
                src = src.strip()
                if src and src not in seen and not src.startswith("data:"):
                    seen.add(src)
                    urls.append(src)
        except Exception:
            continue
        if len(urls) >= 10:
            break
    return urls


# ---------- 画像ダウンロード ----------

def download_images(image_urls: list) -> list:
    Path(IMAGES_DIR).mkdir(exist_ok=True)
    local_paths = []
    for i, url in enumerate(image_urls):
        ext = url.split("?")[0].rsplit(".", 1)[-1] or "jpg"
        dest = os.path.join(IMAGES_DIR, f"image_{i+1}.{ext}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            local_paths.append(dest)
            print(f"  画像 {i+1} ダウンロード完了: {dest}")
        except Exception as e:
            print(f"  画像 {i+1} ダウンロード失敗 ({e}): {url}")
    return local_paths


# ---------- minne 投稿 ----------

def post_to_minne(page, product: dict, local_images: list):
    print("\n[minne] ログイン中 (GMO ID)...")
    page.goto("https://minne.com/users/sign_in", wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.screenshot(path="minne_01_login.png")

    # GMO IDでログイン ボタンをJavaScriptで検索してクリック
    clicked = page.evaluate("""
        () => {
            const candidates = [...document.querySelectorAll('a, button')];
            const btn = candidates.find(el =>
                el.href && (el.href.includes('gmo') || el.href.includes('oauth')) ||
                el.textContent.includes('GMOID') ||
                el.textContent.includes('GMO ID') ||
                el.textContent.includes('GMOIDでログイン') ||
                (el.className && el.className.toString().toLowerCase().includes('gmo'))
            );
            if (btn) { btn.click(); return btn.href || btn.textContent.trim(); }
            return null;
        }
    """)
    print(f"[minne] GMO IDボタン: {clicked}")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    page.screenshot(path="minne_02_gmoid.png")
    print(f"[minne] GMO IDページURL: {page.url}")

    # GMO ID ログインフォーム
    try:
        page.wait_for_selector("input[type='email'], input[type='text'], input[name*='login']", timeout=8000)
    except Exception:
        pass
    _fill(page, [
        "input[type='email']",
        "input[name*='login_id']",
        "input[name*='email']",
        "input[id*='login']",
        "input[type='text']",
    ], MINNE_EMAIL)
    page.wait_for_timeout(500)

    _fill(page, [
        "input[type='password']",
        "input[name*='password']",
        "input[id*='password']",
    ], MINNE_PASSWORD)
    page.wait_for_timeout(500)
    page.screenshot(path="minne_03_gmoid_filled.png")

    _click(page, [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('ログイン')",
        "button:has-text('次へ')",
        "[class*='submit']",
    ])
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)
    page.screenshot(path="minne_04_after_login.png")
    print(f"[minne] ログイン後URL: {page.url}")

    if "sign_in" in page.url or "login" in page.url:
        print("  ※ ログインに失敗した可能性があります。minne_04_after_login.png を確認してください")

    print("[minne] 商品作成ページへ移動...")
    page.goto("https://minne.com/items/new", wait_until="networkidle")
    page.wait_for_timeout(4000)
    page.screenshot(path="minne_04_new_item.png")

    # 商品名
    try:
        page.wait_for_selector("input, textarea", timeout=8000)
    except Exception:
        pass
    _fill(page, [
        "input[name='item[name]']",
        "input[id*='name']",
        "input[placeholder*='商品名']",
        "input[placeholder*='タイトル']",
        "input[placeholder*='name']",
    ], product["title"])
    page.wait_for_timeout(500)

    # 価格
    if product["price"]:
        _fill(page, [
            "input[name='item[price]']",
            "input[id*='price']",
            "input[placeholder*='価格']",
            "input[type='number']",
        ], product["price"])
        page.wait_for_timeout(500)

    # 説明文
    _fill(page, [
        "textarea[name='item[description]']",
        "textarea[id*='description']",
        "textarea[placeholder*='説明']",
        "textarea[placeholder*='商品説明']",
        "textarea",
    ], product["description"])
    page.wait_for_timeout(500)
    page.screenshot(path="minne_05_form_filled.png")

    # 画像アップロード
    if local_images:
        print(f"[minne] 画像アップロード中 ({len(local_images)}枚)...")
        _upload_images(page, local_images, [
            "input[type='file'][accept*='image']",
            "input[type='file']",
        ])
        page.wait_for_timeout(3000)

    # 下書き保存
    print("[minne] 下書き保存中...")
    page.screenshot(path="minne_06_before_save.png")
    _click(page, [
        "button:has-text('下書き保存')",
        "a:has-text('下書き保存')",
        "button:has-text('下書き')",
        "a:has-text('下書き')",
        "button:has-text('保存')",
        "[class*='draft']",
    ])
    page.wait_for_timeout(4000)
    page.screenshot(path="minne_07_after_save.png")
    print(f"[minne] 投稿完了 URL: {page.url}")
    return page.url


# ---------- iichi 投稿 ----------

def post_to_iichi(page, product: dict, local_images: list):
    print("\n[iichi] ログイン中...")
    page.goto("https://www.iichi.com/login", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    _fill(page, ["input[name='email']", "input[type='email']", "#email"], IICHI_EMAIL)
    _fill(page, ["input[name='password']", "input[type='password']", "#password"], IICHI_PASSWORD)
    _click(page, ["button[type='submit']", "input[type='submit']", "button:has-text('ログイン')"])
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    print(f"[iichi] ログイン後URL: {page.url}")

    print("[iichi] 商品作成ページへ移動...")
    page.goto("https://www.iichi.com/listing/item/new", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # 商品名
    _fill(page, [
        "input[name='title']", "#title",
        "input[placeholder*='商品名']", "input[placeholder*='タイトル']",
    ], product["title"])
    page.wait_for_timeout(400)

    # 価格
    if product["price"]:
        _fill(page, [
            "input[name='price']", "#price",
            "input[placeholder*='価格']", "input[type='number']",
        ], product["price"])
        page.wait_for_timeout(400)

    # 説明文
    _fill(page, [
        "textarea[name='description']", "#description",
        "textarea[placeholder*='説明']",
    ], product["description"])
    page.wait_for_timeout(400)

    # 画像アップロード
    if local_images:
        print(f"[iichi] 画像アップロード中 ({len(local_images)}枚)...")
        _upload_images(page, local_images, [
            "input[type='file'][accept*='image']",
            "input[type='file']",
        ])

    # 下書き保存
    print("[iichi] 下書き保存中...")
    _click(page, [
        "button:has-text('下書き保存')",
        "button:has-text('下書き')",
        "a:has-text('下書き')",
        "button:has-text('保存')",
    ])
    page.wait_for_timeout(3000)
    print(f"[iichi] 投稿完了 URL: {page.url}")
    return page.url


# ---------- ユーティリティ ----------

def _fill(page, selectors: list, value: str):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.fill(value, timeout=3000)
                return
        except Exception:
            continue
    print(f"  警告: 入力フィールドが見つかりませんでした ({selectors[0]})")


def _click(page, selectors: list):
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.click(timeout=3000)
                return
        except Exception:
            continue
    print(f"  警告: ボタンが見つかりませんでした ({selectors[0]})")


def _upload_images(page, local_paths: list, selectors: list):
    for sel in selectors:
        try:
            inputs = page.locator(sel)
            if inputs.count() > 0:
                # 複数ファイルを一括セット試行
                try:
                    inputs.first.set_input_files(local_paths[:5], timeout=5000)
                    page.wait_for_timeout(3000)
                    return
                except Exception:
                    # 1枚ずつ試行
                    for path in local_paths[:5]:
                        try:
                            inputs.first.set_input_files(path, timeout=5000)
                            page.wait_for_timeout(2000)
                        except Exception:
                            pass
                    return
        except Exception:
            continue
    print("  警告: 画像アップロード用 file input が見つかりませんでした")


# ---------- メイン ----------

def main():
    if len(sys.argv) < 2:
        print("使い方: python creema_cross_post.py <CreemaのURL> [投稿先]")
        print(f"  投稿先: {', '.join(SUPPORTED_SITES)}  (省略時: minne)")
        print("例: python creema_cross_post.py https://www.creema.jp/item/1234567 minne")
        sys.exit(1)

    creema_url = sys.argv[1]
    target     = sys.argv[2].lower() if len(sys.argv) > 2 else "minne"

    if target not in SUPPORTED_SITES:
        print(f"エラー: 未対応の投稿先「{target}」")
        print(f"対応サイト: {', '.join(SUPPORTED_SITES)}")
        sys.exit(1)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page    = browser.new_page()

        # Step 1: Creema から商品情報取得
        product = scrape_creema(page, creema_url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(product, f, ensure_ascii=False, indent=2)
        print(f"商品情報を {OUTPUT_FILE} に保存しました")

        # Step 2: 画像ダウンロード
        print(f"\n画像をダウンロード中 ({len(product['images'])}枚)...")
        local_images = download_images(product["images"])

        # Step 3: 投稿
        if target == "minne":
            result_url = post_to_minne(page, product, local_images)
        elif target == "iichi":
            result_url = post_to_iichi(page, product, local_images)

        browser.close()

    print(f"\n===== 完了 =====")
    print(f"Creema元URL : {creema_url}")
    print(f"投稿先      : {target}")
    print(f"結果URL     : {result_url}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        msg = traceback.format_exc()
        print("ERROR:", msg)
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(msg)
        print("error.log に保存しました")
    input("\nEnterキーで終了...")
