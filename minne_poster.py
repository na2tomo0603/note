#!/usr/bin/env python3
"""
Minne 商品自動登録
PlaywrightでMinneに商品を下書き登録する
"""

import os
import time


MINNE_EMAIL    = os.environ.get("MINNE_EMAIL", "")
MINNE_PASSWORD = os.environ.get("MINNE_PASSWORD", "")


def post_product(product_dict: dict, image_paths: list, log=print, headless: bool = True):
    """
    Minneに商品を登録して下書き保存する。

    product_dict: CreemaProduct.to_dict() の出力
    image_paths:  ローカル画像ファイルのパスリスト
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    email    = MINNE_EMAIL    or product_dict.get("_minne_email", "")
    password = MINNE_PASSWORD or product_dict.get("_minne_password", "")

    if not email or not password:
        raise ValueError("Minneのメールアドレスとパスワードを設定してください")

    with sync_playwright() as p:
        log("ブラウザ起動中...")
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 390, "height": 844})

        # ── ログイン ──
        log("Minneにログイン中...")
        page.goto("https://minne.com/login", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        page.fill("input[type='email'], input[name='email'], #email", email)
        page.wait_for_timeout(300)
        page.fill("input[type='password'], input[name='password'], #password", password)
        page.wait_for_timeout(300)
        page.click("button[type='submit'], input[type='submit'], button:has-text('ログイン')")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)
        log(f"ログイン完了: {page.url}")

        # ── 商品登録ページへ ──
        log("商品登録ページへ移動...")
        page.goto("https://minne.com/items/new", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        log(f"現在のURL: {page.url}")

        # ── 画像アップロード ──
        if image_paths:
            log(f"画像をアップロード中（{len(image_paths)}枚）...")
            try:
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(image_paths[:5])  # Minneは最大5枚
                page.wait_for_timeout(4000)
                log("画像アップロード完了")
            except Exception as e:
                log(f"画像アップロード失敗（手動で追加してください）: {e}")

        # ── タイトル ──
        title = product_dict.get("title", "")
        if title:
            log("タイトルを入力中...")
            for sel in [
                "input[name='name']",
                "input[placeholder*='タイトル']",
                "input[placeholder*='作品名']",
                "#item_name",
                "input[name='item[name]']",
            ]:
                try:
                    page.fill(sel, title[:60], timeout=3000)  # Minneは60文字制限
                    log(f"タイトル入力: {title[:60]}")
                    break
                except PWTimeout:
                    continue

        # ── 説明文 ──
        description = product_dict.get("description", "")
        if description:
            log("説明文を入力中...")
            for sel in [
                "textarea[name='description']",
                "textarea[placeholder*='説明']",
                "textarea[placeholder*='作品について']",
                "#item_description",
                "textarea[name='item[description]']",
            ]:
                try:
                    page.fill(sel, description[:1000], timeout=3000)
                    log(f"説明文入力: {len(description)}文字")
                    break
                except PWTimeout:
                    continue

        # ── 価格 ──
        price = product_dict.get("price", 0)
        if price > 0:
            log(f"価格を入力中: ¥{price}")
            for sel in [
                "input[name='price']",
                "input[placeholder*='価格']",
                "#item_price",
                "input[name='item[price]']",
            ]:
                try:
                    page.fill(sel, str(price), timeout=3000)
                    log(f"価格入力: ¥{price}")
                    break
                except PWTimeout:
                    continue

        # ── 在庫数 ──
        stock = product_dict.get("stock", 1)
        for sel in [
            "input[name='quantity']",
            "input[name='stock']",
            "input[placeholder*='在庫']",
            "#item_quantity",
        ]:
            try:
                page.fill(sel, str(stock), timeout=3000)
                log(f"在庫数入力: {stock}")
                break
            except PWTimeout:
                continue

        page.wait_for_timeout(1000)

        # ── 下書き保存 ──
        log("下書き保存中...")
        for sel in [
            "button:has-text('下書き保存')",
            "input[value='下書き保存']",
            "button:has-text('下書き')",
            "a:has-text('下書き保存')",
        ]:
            try:
                page.click(sel, timeout=5000)
                page.wait_for_timeout(3000)
                log(f"下書き保存完了: {page.url}")
                break
            except PWTimeout:
                continue

        result_url = page.url
        page.screenshot(path="minne_result.png")
        log("スクリーンショット保存: minne_result.png")

        browser.close()

    return result_url
