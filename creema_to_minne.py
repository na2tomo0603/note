#!/usr/bin/env python3
"""
Creema商品ページ → ミンネ新規出品スクリプト
使い方: python creema_to_minne.py <CreemaのURL>
"""

import sys
import os
import re
import time
import traceback
import urllib.request
from pathlib import Path

MINNE_EMAIL    = os.environ.get("MINNE_EMAIL", "")
MINNE_PASSWORD = os.environ.get("MINNE_PASSWORD", "")


def scrape_creema(page, url):
    """Creema商品ページから情報を取得"""
    print(f"Creemaページ取得中: {url}")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    result = {}

    # タイトル
    for sel in ["h1.p-item-detail__title", "h1[class*='title']", "h1"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                result["title"] = el.inner_text().strip()
                break
        except Exception:
            continue
    result.setdefault("title", "商品タイトル")

    # 価格（数字のみ抽出）
    for sel in [
        "[class*='price']",
        "[class*='Price']",
        "span:has-text('¥')",
        "p:has-text('円')",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                text = el.inner_text()
                nums = re.findall(r"[\d,]+", text.replace("¥", "").replace("円", ""))
                if nums:
                    result["price"] = nums[0].replace(",", "")
                    break
        except Exception:
            continue
    result.setdefault("price", "")

    # 説明文
    for sel in [
        "[class*='description']",
        "[class*='Description']",
        "[class*='detail__body']",
        "[class*='item-detail']",
        "div.p-item-detail__description",
    ]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                text = el.inner_text().strip()
                if len(text) > 10:
                    result["description"] = text
                    break
        except Exception:
            continue
    result.setdefault("description", "")

    # 画像URL（最大5枚）
    image_urls = []
    for sel in [
        "img[class*='item'][src*='creema']",
        "img[class*='photo'][src*='creema']",
        "[class*='gallery'] img",
        "[class*='slider'] img",
        "[class*='thumb'] img",
        ".p-item-detail__image img",
    ]:
        try:
            imgs = page.locator(sel).all()
            for img in imgs:
                src = img.get_attribute("src") or img.get_attribute("data-src") or ""
                # サムネイル→元画像に変換（クエリパラメータ除去）
                src = src.split("?")[0]
                if src and src not in image_urls and "creema" in src:
                    image_urls.append(src)
                if len(image_urls) >= 5:
                    break
        except Exception:
            continue
        if len(image_urls) >= 5:
            break

    # フォールバック: og:imageメタタグ
    if not image_urls:
        try:
            og = page.locator("meta[property='og:image']").get_attribute("content")
            if og:
                image_urls.append(og.split("?")[0])
        except Exception:
            pass

    result["image_urls"] = image_urls

    print(f"タイトル: {result['title']}")
    print(f"価格: {result['price']}円")
    print(f"説明: {result['description'][:80]}...")
    print(f"画像: {len(image_urls)}枚")

    return result


def download_images(image_urls):
    """画像をローカルに保存して絶対パスのリストを返す"""
    paths = []
    tmp_dir = Path("minne_images_tmp")
    tmp_dir.mkdir(exist_ok=True)

    for i, url in enumerate(image_urls):
        ext = url.rsplit(".", 1)[-1] if "." in url else "jpg"
        ext = ext[:4]  # 安全のため
        local_path = tmp_dir / f"item_{i}.{ext}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                local_path.write_bytes(resp.read())
            print(f"画像保存: {local_path}")
            paths.append(str(local_path.resolve()))
        except Exception as e:
            print(f"画像取得失敗 ({url}): {e}")

    return paths


def login_minne(page, email, password):
    """ミンネにログイン"""
    print("ミンネにログイン中...")
    page.goto("https://minne.com/login", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    # メールアドレス入力
    for sel in ["input[type='email']", "input[name='email']", "input[id*='email']"]:
        try:
            page.fill(sel, email, timeout=3000)
            break
        except Exception:
            continue

    page.wait_for_timeout(300)

    # パスワード入力
    for sel in ["input[type='password']", "input[name='password']"]:
        try:
            page.fill(sel, password, timeout=3000)
            break
        except Exception:
            continue

    page.wait_for_timeout(300)

    # ログインボタン
    for sel in ["button[type='submit']", "input[type='submit']", "button:has-text('ログイン')"]:
        try:
            page.click(sel, timeout=3000)
            break
        except Exception:
            continue

    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    print(f"ログイン後URL: {page.url}")


def create_minne_listing(page, item, image_paths):
    """ミンネ新規出品フォームに入力"""
    print("新規出品ページへ移動...")
    page.goto("https://minne.com/items/new", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    page.screenshot(path="minne_new_item.png")
    print("スクリーンショット: minne_new_item.png")

    # 画像アップロード
    if image_paths:
        print(f"画像アップロード中 ({len(image_paths)}枚)...")
        file_inputs = page.locator("input[type='file']")
        count = file_inputs.count()
        print(f"  ファイル入力: {count}個")
        if count > 0:
            try:
                file_inputs.first.set_input_files(image_paths[:5])
                page.wait_for_timeout(5000)
                print("  画像アップロード完了")
            except Exception as e:
                print(f"  画像アップロード失敗: {e}")

    # 商品名
    print("商品名入力中...")
    for sel in [
        "input[name='name']",
        "input[placeholder*='商品名']",
        "input[id*='name']",
        "input[class*='name']",
    ]:
        try:
            page.fill(sel, item["title"], timeout=3000)
            print(f"  商品名: {item['title']}")
            break
        except Exception:
            continue

    page.wait_for_timeout(500)

    # 説明文
    if item["description"]:
        print("説明文入力中...")
        for sel in [
            "textarea[name='description']",
            "textarea[placeholder*='説明']",
            "textarea[id*='description']",
            "textarea",
        ]:
            try:
                page.fill(sel, item["description"], timeout=3000)
                print(f"  説明: {item['description'][:40]}...")
                break
            except Exception:
                continue

    page.wait_for_timeout(500)

    # 価格
    if item["price"]:
        print(f"価格入力中: {item['price']}円")
        for sel in [
            "input[name='price']",
            "input[placeholder*='価格']",
            "input[id*='price']",
            "input[type='number']",
        ]:
            try:
                page.fill(sel, item["price"], timeout=3000)
                print(f"  価格: {item['price']}円")
                break
            except Exception:
                continue

    page.wait_for_timeout(500)
    page.screenshot(path="minne_filled.png")
    print("スクリーンショット: minne_filled.png")

    # 下書き保存
    print("下書き保存中...")
    for sel in [
        "button:has-text('下書き保存')",
        "button:has-text('下書き')",
        "input[value*='下書き']",
        "a:has-text('下書き保存')",
    ]:
        try:
            page.click(sel, timeout=5000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)
            print("下書き保存完了")
            break
        except Exception:
            continue

    print(f"\n完了！URL: {page.url}")
    page.screenshot(path="minne_done.png")
    print("スクリーンショット: minne_done.png")


def safe_input(prompt):
    if sys.stdin.isatty():
        return input(prompt).strip()
    return ""


def main():
    if len(sys.argv) < 2:
        url = safe_input("CreemaのURL: ")
    else:
        url = sys.argv[1]

    if "creema.jp" not in url:
        print("ERROR: CreemaのURLを入力してください (例: https://www.creema.jp/item/XXXXXXX)")
        sys.exit(1)

    email = MINNE_EMAIL
    password = MINNE_PASSWORD

    if not email:
        email = safe_input("ミンネのメールアドレス: ")
    if not password:
        import getpass
        password = getpass.getpass("ミンネのパスワード: ") if sys.stdin.isatty() else ""

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        print("ブラウザ起動中...")
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True,
        )
        page = context.new_page()

        # Creema商品情報取得
        item = scrape_creema(page, url)

        # 画像ダウンロード
        image_paths = []
        if item["image_urls"]:
            print("\n画像をダウンロード中...")
            image_paths = download_images(item["image_urls"])

        # ミンネログイン
        login_minne(page, email, password)

        # 出品フォーム入力
        create_minne_listing(page, item, image_paths)

        if sys.stdin.isatty():
            input("\nEnterキーでブラウザを閉じます...")
        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        msg = traceback.format_exc()
        print("ERROR:", msg)
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(msg)
        print("error.log に保存しました")
    if sys.stdin.isatty():
        input("\nEnterキーで終了...")
