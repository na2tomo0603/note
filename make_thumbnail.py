#!/usr/bin/env python3
"""note.com推奨サイズ(1280x670)のサムネイルを生成する"""

from PIL import Image, ImageDraw, ImageFont
import textwrap

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUT_PATH  = "thumbnail.png"
W, H      = 1280, 670

TITLE    = "シニア世代が\nSNS不要で稼ぐ方法"
SUBTITLE = "note一択な理由"
BADGE    = "副業 × 在宅ワーク × 初心者OK"

BG_TOP    = (15, 32, 80)    # 濃紺
BG_BOTTOM = (40, 80, 160)   # 青
ACCENT    = (255, 180, 0)   # ゴールド
WHITE     = (255, 255, 255)
LIGHT     = (200, 220, 255)


def draw_gradient(draw, w, h, top, bottom):
    for y in range(h):
        ratio = y / h
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def main():
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # グラデーション背景
    draw_gradient(draw, W, H, BG_TOP, BG_BOTTOM)

    # 装飾ライン
    draw.rectangle([0, 0, 8, H], fill=ACCENT)
    draw.rectangle([0, H - 8, W, H], fill=ACCENT)

    # アクセント四角
    draw.rectangle([60, 60, 480, 110], fill=ACCENT)
    font_badge = ImageFont.truetype(FONT_PATH, 30)
    draw.text((70, 68), BADGE, font=font_badge, fill=BG_TOP)

    # メインタイトル
    font_title = ImageFont.truetype(FONT_PATH, 88)
    draw.text((60, 140), TITLE, font=font_title, fill=WHITE, spacing=16)

    # サブタイトル
    font_sub = ImageFont.truetype(FONT_PATH, 52)
    draw.text((60, 430), f"─ {SUBTITLE} ─", font=font_sub, fill=ACCENT)

    # 右下ロゴ風テキスト
    font_logo = ImageFont.truetype(FONT_PATH, 28)
    draw.text((W - 260, H - 55), "働かない働き方", font=font_logo, fill=LIGHT)

    img.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}  ({W}x{H}px)")


if __name__ == "__main__":
    main()
