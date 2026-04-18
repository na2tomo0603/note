#!/usr/bin/env python3
"""
YouTube動画を文字起こしして note.com に下書き投稿するスクリプト
使い方: python youtube_to_note.py <YouTube URL>
"""

import sys
import re
import traceback

EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"
USER_ID  = "na2tomo0603"


def get_video_id(url):
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if not m:
        print("ERROR: YouTube URLが正しくありません")
        sys.exit(1)
    return m.group(1)


def get_transcript(video_id):
    from youtube_transcript_api import YouTubeTranscriptApi
    api = YouTubeTranscriptApi()
    try:
        t = api.fetch(video_id, languages=["ja"])
        print("日本語字幕を取得しました")
    except Exception:
        try:
            t = api.fetch(video_id, languages=["en"])
            print("英語字幕を取得しました")
        except Exception as e:
            print(f"字幕の取得に失敗しました: {e}")
            sys.exit(1)
    return " ".join([s.text.strip() for s in t])


def format_article(raw_text, title):
    """Claude APIで記事に整形（APIキーがない場合はそのまま使用）"""
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY が未設定のため、字幕をそのまま使用します")
        # 基本的な整形のみ
        text = re.sub(r"\s+", " ", raw_text).strip()
        # 句点で改行
        text = text.replace("。", "。\n\n")
        return text

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    print("Claude APIで記事に整形中...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""以下はYouTube動画「{title}」の文字起こしです。
これをnote.comに投稿する読みやすいブログ記事に整形してください。

要件：
- 1000〜1500文字程度
- 見出しを使って構造化する
- 話し言葉を書き言葉に変換する
- 動画の内容を忠実に要約する
- タイトルは含めない（本文のみ）

文字起こし：
{raw_text[:8000]}"""
        }]
    )
    return message.content[0].text


def post_to_note(title, body):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("note.com にログイン中...")
        page.goto("https://note.com/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.fill("input[type='email'], input[id='email']", EMAIL)
        page.wait_for_timeout(500)
        page.fill("input[type='password']", PASSWORD)
        page.wait_for_timeout(500)
        page.click("button[type='submit'], button:has-text('ログイン')")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        print("記事作成ページへ移動中...")
        page.goto("https://note.com/notes/new", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        print("タイトルを入力中...")
        title_sel = "textarea, input[placeholder*='タイトル'], [data-placeholder*='タイトル']"
        page.wait_for_selector(title_sel, timeout=10000)
        page.click(title_sel)
        page.keyboard.type(title)
        page.wait_for_timeout(500)

        print("本文を入力中...")
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        page.keyboard.type(body)
        page.wait_for_timeout(1000)

        print("下書き保存中...")
        try:
            page.click("button:has-text('下書き保存'), button:has-text('保存')", timeout=5000)
        except PWTimeout:
            page.keyboard.press("Control+s")
        page.wait_for_timeout(3000)

        print()
        print("SUCCESS! 下書き保存しました")
        print(f"URL: {page.url}")
        browser.close()


def main():
    if len(sys.argv) < 2:
        print("使い方: python youtube_to_note.py <YouTube URL>")
        sys.exit(1)

    url = sys.argv[1]
    video_id = get_video_id(url)
    print(f"動画ID: {video_id}")

    print("字幕を取得中...")
    raw_text = get_transcript(video_id)
    print(f"取得完了（{len(raw_text)}文字）")

    # タイトルを動画IDから仮設定（Claude APIがあれば改善可）
    title = f"【動画まとめ】{video_id}"

    body = format_article(raw_text, title)
    print(f"記事整形完了（{len(body)}文字）")
    print()
    print("=== 記事プレビュー（最初の200文字）===")
    print(body[:200])
    print("...")

    post_to_note(title, body)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        msg = traceback.format_exc()
        print("ERROR:", msg)
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(msg)
        print("error.log に保存しました")
    input("Press Enter to exit...")
