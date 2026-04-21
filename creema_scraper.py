#!/usr/bin/env python3
"""
Creema 商品ページスクレイパー
PlaywrightでCreemaの商品情報を取得する
"""

import re
import json
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import List


@dataclass
class CreemaProduct:
    title: str = ""
    description: str = ""
    price: int = 0
    images: List[str] = field(default_factory=list)
    category: str = ""
    tags: List[str] = field(default_factory=list)
    stock: int = 1
    url: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "images": self.images,
            "category": self.category,
            "tags": self.tags,
            "stock": self.stock,
            "url": self.url,
        }


def scrape(url: str, log=print) -> CreemaProduct:
    """CreemaのURLから商品情報を取得する"""
    from playwright.sync_api import sync_playwright

    product = CreemaProduct(url=url)

    with sync_playwright() as p:
        log("ブラウザ起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            )
        )

        log(f"Creemaページ読み込み中: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # ── タイトル ──
        for sel in [
            "h1.item-name",
            "h1[class*='item']",
            "h1[class*='title']",
            "h1",
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    product.title = el.inner_text().strip()
                    if product.title:
                        log(f"タイトル: {product.title}")
                        break
            except Exception:
                pass

        # ── 価格 ──
        for sel in [
            "[class*='price']",
            "[class*='Price']",
            "span.price",
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    text = el.inner_text()
                    nums = re.findall(r"[\d,]+", text)
                    if nums:
                        product.price = int(nums[0].replace(",", ""))
                        log(f"価格: ¥{product.price}")
                        break
            except Exception:
                pass

        # ── 説明文 ──
        for sel in [
            "[class*='description']",
            "[class*='Description']",
            "[class*='detail']",
            ".item-detail",
            "p.description",
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    text = el.inner_text().strip()
                    if len(text) > 10:
                        product.description = text
                        log(f"説明文: {len(text)}文字")
                        break
            except Exception:
                pass

        # ── 画像URL ──
        try:
            imgs = page.locator("img[src*='creema']").all()
            seen = set()
            for img in imgs:
                src = img.get_attribute("src") or ""
                # サムネより大きい画像を優先
                if any(k in src for k in ["/uploads/", "/products/"]) and src not in seen:
                    # 大きいサイズのURLに変換を試みる
                    large = re.sub(r"_\d+x\d+\.", "_1000x1000.", src)
                    product.images.append(large)
                    seen.add(src)
                if len(product.images) >= 10:
                    break
            log(f"画像: {len(product.images)}枚")
        except Exception as e:
            log(f"画像取得エラー: {e}")

        # ── カテゴリ ──
        for sel in [
            "[class*='category']",
            "[class*='breadcrumb'] a",
            "nav a",
        ]:
            try:
                items = page.locator(sel).all()
                cats = [el.inner_text().strip() for el in items if el.inner_text().strip()]
                if cats:
                    product.category = cats[-1]
                    log(f"カテゴリ: {product.category}")
                    break
            except Exception:
                pass

        # ── タグ ──
        for sel in ["[class*='tag'] a", "[class*='Tag'] a", "a[href*='/tags/']"]:
            try:
                items = page.locator(sel).all()
                product.tags = [el.inner_text().strip() for el in items[:10]]
                if product.tags:
                    log(f"タグ: {product.tags}")
                    break
            except Exception:
                pass

        browser.close()

    return product


def download_images(product: CreemaProduct, save_dir: str = "tmp_images", log=print) -> List[str]:
    """商品画像をローカルに保存し、ファイルパスのリストを返す"""
    os.makedirs(save_dir, exist_ok=True)
    paths = []
    for i, url in enumerate(product.images):
        ext = "jpg" if ".jpg" in url.lower() else "png"
        path = os.path.join(save_dir, f"product_{i+1}.{ext}")
        try:
            urllib.request.urlretrieve(url, path)
            paths.append(path)
            log(f"画像保存: {path}")
        except Exception as e:
            log(f"画像{i+1}のダウンロード失敗: {e}")
    return paths
