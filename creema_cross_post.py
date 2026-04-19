#!/usr/bin/env python3
"""Creema商品を他のハンドメイドサイトにクロスポストするスクリプト"""
import sys
import os
import json
import re
import traceback
import urllib.request
from pathlib import Path

MINNE_SESSION  = "session_minne.json"
IICHI_SESSION  = "session_iichi.json"
IMAGES_DIR     = "creema_images"
OUTPUT_FILE    = "creema_product.json"
SUPPORTED_SITES = ["minne", "iichi"]


# ---------- Creema スクレイピング ----------

def scrape_creema(page, url: str) -> dict:
    print(f"[Creema] 商品ページを取得中: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    # タイトル
    title = _extract_text(page, ["h1[class*='name']", "h1[class*='title']", "h1"])

    # 価格 — メイン商品エリアのみ、最初に見つかった数値を使用
    price_raw = page.evaluate("""
        () => {
            // カートボタン周辺の価格を優先して取得
            const candidates = [
                ...document.querySelectorAll('[class*="price"], [class*="Price"]')
            ];
            for (const el of candidates) {
                const text = el.innerText || '';
                const m = text.match(/[1-9][\\d,]+/);
                if (m) return m[0].replace(/,/g, '');
            }
            return '';
        }
    """)
    price_clean = re.sub(r"[^\d]", "", price_raw or "")

    # 説明文
    description = _extract_text(page, [
        "[class*='ItemDescription']",
        "[class*='itemDescription']",
        "[class*='item-description']",
        "[class*='description']",
    ])

    # 画像 — メイン商品ギャラリーのみ（関連商品除外）、高解像度URL
    images = page.evaluate("""
        () => {
            const seen = new Set();
            const urls = [];

            // ページ上部の大きな画像だけを取得（関連商品セクション前まで）
            const stopWords = ['おすすめ', '関連', 'ランキング', 'related', 'recommend'];
            const allEls = [...document.querySelectorAll('*')];
            let stopIdx = allEls.length;
            for (let i = 0; i < allEls.length; i++) {
                const txt = allEls[i].textContent.trim();
                if (stopWords.some(w => txt.startsWith(w)) && allEls[i].tagName.match(/^H[2-4]$/)) {
                    stopIdx = i;
                    break;
                }
            }

            const imgs = [...document.querySelectorAll('img')];
            for (const img of imgs) {
                // 関連商品セクション以降はスキップ
                let skip = false;
                for (let i = stopIdx; i < allEls.length; i++) {
                    if (allEls[i] === img) { skip = true; break; }
                }
                if (skip) break;

                const src = (img.src || img.dataset.src || '').split('?')[0];
                if (!src || src.startsWith('data:') || seen.has(src)) continue;
                // アイコン・アバター・ロゴは除外
                if (/avatar|icon|logo|header|footer/i.test(src)) continue;
                // 小さい画像は除外
                if ((img.naturalWidth && img.naturalWidth < 150) ||
                    (img.naturalHeight && img.naturalHeight < 150)) continue;

                seen.add(src);
                urls.push(src);
                if (urls.length >= 10) break;
            }
            return urls;
        }
    """)

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

def post_to_minne(page, context, product: dict, local_images: list):
    # ログイン確認（セッションがあれば自動でログイン済み）
    print("\n[minne] ログイン状態を確認中...")
    try:
        page.goto("https://minne.com/account", wait_until="domcontentloaded", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    if "sign_in" in page.url or "login" in page.url:
        print("\n" + "="*50)
        print("【ブラウザでminneにログインしてください】")
        print("ログイン完了後、このターミナルに戻ってEnterを押してください")
        print("="*50)
        input("ログイン完了後、Enterキーを押してください... ")
        page.wait_for_timeout(2000)
        # セッションを保存（次回から自動ログイン）
        context.storage_state(path=MINNE_SESSION)
        print("✓ セッションを保存しました（次回から自動ログイン）")
    else:
        print("[minne] ログイン済みです")

    # 出品ページへ自動移動
    print("[minne] 出品ページを探しています...")
    listing_url = None
    for url in ["https://minne.com/account/products/new", "https://minne.com/works/new"]:
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
        print("\n" + "="*50)
        print("【出品フォームを手動で開いてください】")
        print("ブラウザで「作品を出品する」を開いてEnterを押してください")
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
        "input[name='item[name]']", "input[id*='name']",
        "input[placeholder*='商品名']", "input[placeholder*='タイトル']",
    ], product["title"])
    page.wait_for_timeout(500)

    if product["price"]:
        _fill(page, [
            "input[name='item[price]']", "input[id*='price']",
            "input[placeholder*='価格']", "input[type='number']",
        ], product["price"])
        page.wait_for_timeout(500)

    _fill(page, [
        "textarea[name='item[description]']", "textarea[id*='description']",
        "textarea[placeholder*='説明']", "textarea",
    ], product["description"])
    page.wait_for_timeout(500)
    page.screenshot(path="minne_form_filled.png")

    if local_images:
        print(f"[minne] 画像アップロード中 ({len(local_images)}枚)...")
        _upload_images(page, local_images, [
            "input[type='file'][accept*='image']", "input[type='file']",
        ])
        page.wait_for_timeout(3000)

    print("[minne] 保存中...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    page.screenshot(path="minne_before_save.png")
    _click(page, [
        "button:has-text('非公開で保存')", "a:has-text('非公開で保存')",
        "button:has-text('非公開')", "button:has-text('下書き保存')",
        "button:has-text('下書き')", "button:has-text('保存')",
        "button:has-text('出品する')", "[class*='draft']", "[class*='save']",
    ])
    page.wait_for_timeout(4000)
    page.screenshot(path="minne_after_save.png")
    print(f"[minne] 投稿完了 URL: {page.url}")
    return page.url


# ---------- iichi 投稿 ----------

def post_to_iichi(page, context, product: dict, local_images: list):
    print("\n[iichi] ログイン状態を確認中...")
    try:
        page.goto("https://www.iichi.com/mypage", wait_until="domcontentloaded", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    if "login" in page.url or "signin" in page.url.lower():
        print("\n[iichi] 自動ログインを試みています...")
        try:
            page.goto("https://www.iichi.com/login", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        page.screenshot(path="iichi_login.png")

        # ログインフォームを探す
        email_filled = False
        for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']"]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    # Yahoo IDでログインの可能性があるので確認
                    page.screenshot(path="iichi_login_form.png")
                    el.fill(os.environ.get("IICHI_EMAIL", "na2ko0710@yahoo.co.jp"), timeout=3000)
                    email_filled = True
                    break
            except Exception:
                continue

        if email_filled:
            for sel in ["input[type='password']", "input[name*='password']"]:
                try:
                    el = page.locator(sel).first
                    if el.count() > 0:
                        el.fill(os.environ.get("IICHI_PASSWORD", "na2tomo0603"), timeout=3000)
                        break
                except Exception:
                    continue
            _click(page, ["button[type='submit']", "input[type='submit']", "button:has-text('ログイン')"])
            page.wait_for_timeout(4000)

        if "login" in page.url or "signin" in page.url.lower():
            print("\n" + "="*50)
            print("【ブラウザでiichiにログインしてください】")
            print("ログイン完了後、Enterを押してください")
            print("="*50)
            input("ログイン完了後、Enterキーを押してください... ")
            page.wait_for_timeout(2000)

        context.storage_state(path=IICHI_SESSION)
        print("✓ セッションを保存しました（次回から自動ログイン）")
    else:
        print("[iichi] ログイン済みです")

    # 出品ページへ自動移動
    print("[iichi] 出品ページを探しています...")
    listing_url = None
    for url in ["https://www.iichi.com/listing/item/new", "https://www.iichi.com/items/new"]:
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
        print("【出品フォームを手動で開いてください】")
        print("ブラウザでiichiの出品フォームを開いてEnterを押してください")
        print("="*50)
        input("準備できたらEnterキーを押してください... ")
        page.wait_for_timeout(2000)

    page.screenshot(path="iichi_new_item.png")
    print(f"[iichi] 出品ページURL: {page.url}")

    _fill(page, ["input[name='title']", "#title", "input[placeholder*='商品名']"], product["title"])
    page.wait_for_timeout(400)
    if product["price"]:
        _fill(page, ["input[name='price']", "#price", "input[placeholder*='価格']", "input[type='number']"], product["price"])
        page.wait_for_timeout(400)
    _fill(page, ["textarea[name='description']", "#description", "textarea[placeholder*='説明']", "textarea"], product["description"])
    page.wait_for_timeout(400)
    page.screenshot(path="iichi_form_filled.png")

    if local_images:
        print(f"[iichi] 画像アップロード中 ({len(local_images)}枚)...")
        _upload_images(page, local_images, [
            "input[type='file'][accept*='image']", "input[type='file']",
        ])

    print("[iichi] 保存中...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)
    page.screenshot(path="iichi_before_save.png")
    _click(page, [
        "button:has-text('非公開で保存')", "button:has-text('下書き保存')",
        "button:has-text('下書き')", "button:has-text('保存')", "button:has-text('出品する')",
    ])
    page.wait_for_timeout(3000)
    page.screenshot(path="iichi_after_save.png")
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
        sys.exit(1)

    creema_url = sys.argv[1]
    target     = sys.argv[2].lower() if len(sys.argv) > 2 else "minne"

    if target not in SUPPORTED_SITES:
        print(f"エラー: 未対応の投稿先「{target}」")
        sys.exit(1)

    from playwright.sync_api import sync_playwright

    session_file = MINNE_SESSION if target == "minne" else IICHI_SESSION

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if os.path.exists(session_file):
            context = browser.new_context(storage_state=session_file)
            print(f"保存済みセッションを使用します ({session_file})")
        else:
            context = browser.new_context()

        page = context.new_page()

        product = scrape_creema(page, creema_url)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(product, f, ensure_ascii=False, indent=2)
        print(f"商品情報を {OUTPUT_FILE} に保存しました")

        print(f"\n画像をダウンロード中 ({len(product['images'])}枚)...")
        local_images = download_images(product["images"])

        if target == "minne":
            result_url = post_to_minne(page, context, product, local_images)
        elif target == "iichi":
            result_url = post_to_iichi(page, context, product, local_images)

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
