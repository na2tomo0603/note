#!/usr/bin/env python3
"""
/youtube-to-note スキル実行スクリプト
YouTube URL → 文字起こし → 記事整形 → サムネ生成 → article_draft.md 保存
"""

import sys
import re
import os
import textwrap
import traceback


EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"
USER_ID  = "na2tomo0603"

FONT_PATH = None  # 自動検出


def get_video_id(url):
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if not m:
        print("ERROR: YouTube URLが正しくありません")
        sys.exit(1)
    return m.group(1)


def get_transcript(video_id):
    from youtube_transcript_api import YouTubeTranscriptApi
    api = YouTubeTranscriptApi()
    for lang in ["ja", "en"]:
        try:
            t = api.fetch(video_id, languages=[lang])
            text = " ".join([s.text.strip() for s in t])
            print(f"字幕取得完了（{lang}）: {len(text)}文字")
            with open("transcript.txt", "w", encoding="utf-8") as f:
                f.write(text)
            return text
        except Exception:
            continue
    print("ERROR: 字幕を取得できませんでした")
    sys.exit(1)


def get_video_title(video_id):
    """動画タイトルを取得（取得できない場合はIDを返す）"""
    try:
        import urllib.request
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        with urllib.request.urlopen(url, timeout=5) as r:
            import json
            data = json.loads(r.read())
            return data.get("title", video_id)
    except Exception:
        return video_id


def format_article_with_claude(raw_text, video_title):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY未設定 → 基本整形のみ実施")
        return basic_format(raw_text, video_title)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    print("Claude APIで記事・タイトル・タグを生成中...")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": f"""以下はYouTube動画「{video_title}」の文字起こしです。
これをnote.comに投稿する質の高いブログ記事に整形してください。

出力形式（必ずこの形式で）:
===TITLE===
（note記事のタイトル：30文字以内）
===TAGS===
（タグをカンマ区切りで5〜8個）
===BODY===
（本文：5000文字程度、見出し##を5〜8個使って構造化、話し言葉→書き言葉、各セクションを充実させること）

文字起こし:
{raw_text[:12000]}"""
        }]
    )

    output = message.content[0].text
    title = re.search(r"===TITLE===\s*(.+)", output)
    tags  = re.search(r"===TAGS===\s*(.+)", output)
    body  = re.search(r"===BODY===\s*([\s\S]+)", output)

    article_title = title.group(1).strip() if title else video_title
    article_tags  = tags.group(1).strip()  if tags  else ""
    article_body  = body.group(1).strip()  if body  else raw_text[:2000]

    return article_body, article_title, article_tags


def basic_format(raw_text, video_title):
    """APIキーなしでも読みやすい記事に整形する"""
    import re

    # 重複フレーズ・フィラーを除去
    text = re.sub(r'\[.*?\]', '', raw_text)
    text = re.sub(r'(えー+|あの+|まあ+|ちょっと|なんか|そう+ですね)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # 句点で分割して文のリストに
    sentences = [s.strip() for s in re.split(r'[。！？]', text) if len(s.strip()) > 10]

    # 5000文字程度に収める
    body_sentences = []
    total = 0
    for s in sentences:
        if total + len(s) > 5000:
            break
        body_sentences.append(s + '。')
        total += len(s)

    # 5〜6文ごとに段落分け
    paragraphs = []
    chunk = []
    for i, s in enumerate(body_sentences):
        chunk.append(s)
        if (i + 1) % 5 == 0:
            paragraphs.append(''.join(chunk))
            chunk = []
    if chunk:
        paragraphs.append(''.join(chunk))

    # タイトルから見出しキーワードを抽出
    tags_from_title = re.findall(r'【(.+?)】', video_title)

    # 記事本文を組み立て
    section_titles = ["はじめに", "動画の概要", "ポイント解説①", "ポイント解説②", "ポイント解説③", "実践方法", "まとめ"]
    article = ""
    for i, para in enumerate(paragraphs):
        if i < len(section_titles):
            article += f"\n## {section_titles[i]}\n\n"
        article += para + "\n\n"

    return article.strip(), video_title, " ".join(tags_from_title[:6]) if tags_from_title else ""


def make_thumbnail(title_text):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillowが未インストール: pip install pillow")
        return

    W, H = 1280, 670

    # フォント検索
    font_candidates = [
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
    ]
    font_path = next((f for f in font_candidates if os.path.exists(f)), None)

    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # グラデーション背景
    for y in range(H):
        r = int(15 + 25 * y / H)
        g = int(32 + 48 * y / H)
        b = int(80 + 80 * y / H)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # 装飾ライン
    draw.rectangle([0, 0, 8, H], fill=(255, 180, 0))
    draw.rectangle([0, H - 8, W, H], fill=(255, 180, 0))

    if font_path:
        font_badge = ImageFont.truetype(font_path, 30)
        font_title = ImageFont.truetype(font_path, 72)
        font_sub   = ImageFont.truetype(font_path, 36)
    else:
        font_badge = font_title = font_sub = ImageFont.load_default()

    # バッジ
    draw.rectangle([60, 55, 500, 105], fill=(255, 180, 0))
    draw.text((72, 63), "副業 × 在宅ワーク × 初心者OK", font=font_badge, fill=(15, 32, 80))

    # タイトル（長い場合は折り返し）
    short = textwrap.fill(title_text, width=14)
    draw.text((60, 130), short, font=font_title, fill=(255, 255, 255), spacing=14)

    # 右下
    draw.text((W - 280, H - 50), "働かない働き方", font=font_sub, fill=(200, 220, 255))

    img.save("thumbnail.png")
    print("サムネイル生成: thumbnail.png (1280x670)")


def save_article(title, body, tags=""):
    content = f"# {title}\n\n"
    if tags:
        content += f"**タグ:** {tags}\n\n---\n\n"
    content += body
    with open("article_draft.md", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"記事保存: article_draft.md ({len(body)}文字)")


def main():
    if len(sys.argv) < 2:
        print("使い方: python youtube_to_note.py <YouTube URL>")
        sys.exit(1)

    url      = sys.argv[1]
    video_id = get_video_id(url)
    print(f"動画ID: {video_id}")

    print("\n▼ 字幕取得中...")
    raw_text = get_transcript(video_id)

    print("\n▼ 動画タイトル取得中...")
    video_title = get_video_title(video_id)
    print(f"タイトル: {video_title}")

    print("\n▼ 記事整形中...")
    result = format_article_with_claude(raw_text, video_title)
    body, title, tags = (result if len(result) == 3 else (result[0], video_title, ""))

    print("\n▼ サムネイル生成中...")
    make_thumbnail(title)

    print("\n▼ 記事保存中...")
    save_article(title, body, tags)

    print("\n" + "="*40)
    print("完了！次のコマンドでnote.comに投稿できます:")
    print("  python post_to_note.py")
    print("="*40)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        msg = traceback.format_exc()
        print("ERROR:", msg)
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(msg)
    input("\nEnterキーで終了...")
