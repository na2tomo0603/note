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
MINNE_EMAIL    = os.environ.get("MINNE_EMAIL", "na2ko0710@yahoo.co.jp")
MINNE_PASSWORD = os.environ.get("MINNE_PASSWORD", "na2tomo0603")

IICHI_EMAIL    = os.environ.get("IICHI_EMAIL", "na2ko0710@yahoo.co.jp")
IICHI_PASSWORD = os.environ.get("IICHI_PASSWORD", "na2tomo0603")

IMAGES_DIR  = "creema_images"
OUTPUT_FILE = "creema_product.json"

SUPPORTED_SITES = ["minne", "iichi"]


# ---------- Creema スクレイピング ----------

def scrape_creema(page, url: str) -> dict:
    print(f"[Creema] 商品ページを取得中: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception:
        pass
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
    from urllib.parse import urlparse
    Path(IMAGES_DIR).mkdir(exist_ok=True)
    local_paths = []
    for i, url in enumerate(image_urls):
        url_path = urlparse(url).path
        fname = url_path.split("/")[-1]
        raw_ext = fname.rsplit(".", 1)[-1] if "." in fname else ""
        ext = raw_ext if raw_ext and len(raw_ext) <= 4 else "jpg"
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
    print("\n[minne] ログインページを開きます...")
    try:
        page.goto("https://minne.com/users/sign_in", wait_until="domcontentloaded", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    print("\n" + "="*50)
    print("【手動でログインしてください】")
    print("1. 開いたブラウザでminneにログインしてください")
    print("   （GMO ID / Yahoo / Google など好きな方法で）")
    print("2. ログイン後、minneのトップページが表示されたら")
    print("   このターミナルに戻ってきてください")
    print("="*50)
    input("ログイン完了後、Enterキーを押してください... ")
    page.wait_for_timeout(2000)
    print(f"[minne] 現在のURL: {page.url}")

    print("[minne] 出品ページを探しています...")
    listing_url = None
    for url in ["https://minne.com/account/products/new", "https://minne.com/works/new",
                "https://minne.com/seller/items/new", "https://minne.com/listing/new"]:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(2000)
            if page.locator("input, textarea").count() > 2:
                listing_url = url
                print(f"[minne] 出品ページ発見: {url}")
                break
        except Exception:
            continue

    if not listing_url:
        try:
            page.goto("https://minne.com/account", wait_until="domcontentloaded", timeout=10000)
        except Exception:
            pass
        page.evaluate("""
            () => {
                const links = [...document.querySelectorAll('a')];
                const link = links.find(a => a.textContent.includes('出品') || a.href.includes('new'));
                if (link) link.click();
            }
        """)
        page.wait_for_timeout(3000)
        print("\n" + "="*50)
        print("【出品フォームが開きましたか？】")
        print("ブラウザで商品名・価格の入力欄が見えたら")
        print("Enterキーを押してください。")
        print("見えない場合はブラウザで「作品を出品する」を")
        print("クリックしてからEnterを押してください。")
        print("="*50)
        input("準備できたらEnterキーを押してください... ")
        page.wait_for_timeout(2000)

    page.screenshot(path="minne_new_item.png")
    print(f"[minne] 出品ページURL: {page.url}")

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

    if product["price"]:
        _fill(page, [
            "input[name='item[price]']",
            "input[id*='price']",
            "input[placeholder*='価格']",
            "input[type='number']",
        ], product["price"])
        page.wait_for_timeout(500)

    _fill(page, [
        "textarea[name='item[description]']",
        "textarea[id*='description']",
        "textarea[placeholder*='説明']",
        "textarea[placeholder*='商品説明']",
        "textarea",
    ], product["description"])
    page.wait_for_timeout(500)
    page.screenshot(path="minne_form_filled.png")

    if local_images:
        print(f"[minne] 画像アップロード中 ({len(local_images)}枚)...")
        _upload_images(page, local_images, [
            "input[type='file'][accept*='image']",
            "input[type='file']",
        ])
        page.wait_for_timeout(3000)

    print("[minne] 保存中...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    page.screenshot(path="minne_before_save.png")
    _click(page, [
        "button:has-text('非公開で保存')",
        "a:has-text('非公開で保存')",
        "button:has-text('非公開')",
        "button:has-text('下書き保存')",
        "button:has-text('下書き')",
        "button:has-text('保存')",
        "button:has-text('出品する')",
        "[class*='draft']",
        "[class*='save']",
    ])
    page.wait_for_timeout(4000)
    page.screenshot(path="minne_after_save.png")
    print(f"[minne] 投稿完了 URL: {page.url}")
    return page.url


# ---------- iichi 投稿 ----------

def post_to_iichi(page, product: dict, local_images: list):
    print("\n[iichi] ログイン中...")
    try:
        page.goto("https://www.iichi.com/login", wait_until="domcontentloaded", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    page.screenshot(path="iichi_01_login.png")

    _fill(page, ["input[type='email']", "input[name*='email']", "input[id*='email']", "input[type='text']"], IICHI_EMAIL)
    page.wait_for_timeout(400)
    _fill(page, ["input[type='password']", "input[name*='password']", "input[id*='password']"], IICHI_PASSWORD)
    page.wait_for_timeout(400)
    _click(page, ["button[type='submit']", "input[type='submit']", "button:has-text('ログイン')"])
    page.wait_for_timeout(4000)
    page.screenshot(path="iichi_02_after_login.png")
    print(f"[iichi] ログイン後URL: {page.url}")

    if "login" in page.url or "signin" in page.url.lower():
        print("\n" + "="*50)
        print("【手動でログインしてください】")
        print("ブラウザでiichiにログインしてEnterを押してください")
        print("="*50)
        input("ログイン完了後、Enterキーを押してください... ")
        page.wait_for_timeout(2000)

    print("[iichi] 出品ページを探しています...")
    listing_url = None
    for url in ["https://www.iichi.com/listing/item/new", "https://www.iichi.com/items/new",
                "https://www.iichi.com/sell/new"]:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(2000)
            if page.locator("input, textarea").count() > 2:
                listing_url = url
                print(f"[iichi] 出品ページ発見: {url}")
                break
        except Exception:
            continue

    if not listing_url:
        print("\n" + "="*50)
        print("【出品ページを手動で開いてください】")
        print("ブラウザでiichi の出品フォームを開いてください")
        print("="*50)
        input("出品フォームが開いたら、Enterキーを押してください... ")
        page.wait_for_timeout(2000)

    page.screenshot(path="iichi_03_new_item.png")
    print(f"[iichi] 出品ページURL: {page.url}")

    _fill(page, [
        "input[name='title']", "#title",
        "input[placeholder*='商品名']", "input[placeholder*='タイトル']",
    ], product["title"])
    page.wait_for_timeout(400)

    if product["price"]:
        _fill(page, [
            "input[name='price']", "#price",
            "input[placeholder*='価格']", "input[type='number']",
        ], product["price"])
        page.wait_for_timeout(400)

    _fill(page, [
        "textarea[name='description']", "#description",
        "textarea[placeholder*='説明']",
    ], product["description"])
    page.wait_for_timeout(400)

    if local_images:
        print(f"[iichi] 画像アップロード中 ({len(local_images)}枚)...")
        _upload_images(page, local_images, [
            "input[type='file'][accept*='image']",
            "input[type='file']",
        ])

    print("[iichi] 保存中...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    page.screenshot(path="iichi_04_before_save.png")
    _click(page, [
        "button:has-text('非公開で保存')",
        "button:has-text('下書き保存')",
        "button:has-text('下書き')",
        "a:has-text('下書き')",
        "button:has-text('保存')",
        "button:has-text('出品する')",
    ])
    page.wait_for_timeout(3000)
    page.screenshot(path="iichi_05_after_save.png")
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
                try:
                    inputs.first.set_input_files(local_paths[:5], timeout=5000)
                    page.wait_for_timeout(3000)
                    return
                except Exception:
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

        product = scrape_creema(page, creema_url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(product, f, ensure_ascii=False, indent=2)
        print(f"商品情報を {OUTPUT_FILE} に保存しました")

        print(f"\n画像をダウンロード中 ({len(product['images'])}枚)...")
        local_images = download_images(product["images"])

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
