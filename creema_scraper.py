#!/usr/bin/env python3
"""Creema 商品ページスクレイパー（requests + BeautifulSoup）"""

import re
import os
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


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


def scrape(url: str, log=print) -> CreemaProduct:
    import requests
    from bs4 import BeautifulSoup

    product = CreemaProduct(url=url)
    log(f"Creemaページを取得中: {url}")

    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    log("ページ取得完了")

    # タイトル
    for sel in ["h1.item-name", "h1[class*='title']", "h1"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            product.title = el.get_text(strip=True)
            break
    log(f"タイトル: {product.title}")

    # 価格
    for sel in ["[class*='price']", ".price", "span[class*='Price']"]:
        el = soup.select_one(sel)
        if el:
            nums = re.findall(r"[\d,]+", el.get_text())
            if nums:
                product.price = int(nums[0].replace(",", ""))
                break
    log(f"価格: ¥{product.price:,}")

    # 説明文
    for sel in ["[class*='description']", "[class*='detail']", ".item-detail"]:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 10:
            product.description = el.get_text(separator="\n", strip=True)
            break
    log(f"説明文: {len(product.description)}文字")

    # 画像URL
    seen = set()
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if any(k in src for k in ["/uploads/", "/products/", "creema"]):
            large = re.sub(r"_\d+x\d+\.", "_1000x1000.", src)
            if large not in seen:
                product.images.append(large)
                seen.add(large)
        if len(product.images) >= 10:
            break
    log(f"画像: {len(product.images)}枚")

    # カテゴリ
    breadcrumbs = soup.select("[class*='breadcrumb'] a, nav a")
    if breadcrumbs:
        product.category = breadcrumbs[-1].get_text(strip=True)

    # タグ
    for sel in ["a[href*='/tags/']", "[class*='tag'] a"]:
        tags = [t.get_text(strip=True) for t in soup.select(sel)]
        if tags:
            product.tags = tags[:10]
            break

    log("取得完了")
    return product


def download_images(product: CreemaProduct, save_dir: str = "tmp_images", log=print) -> List[str]:
    import requests
    os.makedirs(save_dir, exist_ok=True)
    paths = []
    for i, url in enumerate(product.images):
        ext = "jpg" if ".jpg" in url.lower() or "jpeg" in url.lower() else "png"
        path = os.path.join(save_dir, f"product_{i+1}.{ext}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            with open(path, "wb") as f:
                f.write(r.content)
            paths.append(path)
            log(f"画像保存: {path}")
        except Exception as e:
            log(f"画像{i+1}のDL失敗: {e}")
    return paths
