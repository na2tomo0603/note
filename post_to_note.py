#!/usr/bin/env python3
import sys
import os
import traceback

EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"
THUMBNAIL = "thumbnail.png"


def load_article():
    """article_draft.md からタイトル・本文を自動読み込み"""
    try:
        with open("article_draft.md", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        title = lines[0].lstrip("# ").strip() if lines else "下書き"
        body  = "\n".join(lines[1:]).strip()
        print(f"記事読み込み: {title[:30]}... ({len(body)}文字)")
        return title, body
    except Exception as e:
        print(f"article_draft.md が読み込めません: {e}")
        sys.exit(1)


def type_article(page, body):
    """見出し・本文を入力。insertText()でProseMirrorに制限なく挿入"""
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("## "):
            page.keyboard.type("## ")
            page.wait_for_timeout(200)
            page.keyboard.insert_text(line[3:])
            page.keyboard.press("Enter")
            page.wait_for_timeout(300)

        elif line.strip() == "":
            page.keyboard.press("Enter")
            page.wait_for_timeout(100)

        else:
            para_lines = []
            while i < len(lines) and lines[i].strip() != "" and not lines[i].startswith("## "):
                para_lines.append(lines[i])
                i += 1
            page.keyboard.insert_text("\n".join(para_lines))
            page.keyboard.press("Enter")
            page.keyboard.press("Enter")
            page.wait_for_timeout(300)
            continue

        i += 1


def upload_thumbnail(page, path):
    if not os.path.exists(path):
        print("thumbnail.png なし → スキップ")
        return

    abs_path = os.path.abspath(path)
    page.screenshot(path="screen_before_thumb.png")
    print("スクリーンショット: screen_before_thumb.png")

    # 非表示のfile inputを直接操作
    file_inputs = page.locator("input[type='file']")
    count = file_inputs.count()
    print(f"file input: {count}個")

    if count > 0:
        try:
            file_inputs.first.set_input_files(abs_path)
            page.wait_for_timeout(3000)
            print("サムネイルアップロード完了")
            return
        except Exception as e:
            print(f"直接セット失敗: {e}")

    try:
        with page.expect_file_chooser(timeout=6000) as fc_info:
            for sel in ["button:has-text('カバー')", "button:has-text('画像')",
                        "[class*='cover'] button", "[class*='thumbnail'] button"]:
                try:
                    page.click(sel, timeout=2000)
                    break
                except Exception:
                    continue
        fc_info.value.set_files(abs_path)
        page.wait_for_timeout(3000)
        print("サムネイルアップロード完了")
    except Exception as e:
        print(f"サムネイル失敗: {e}")
        print("→ 手動でカバー画像を設定してください（screen_before_thumb.png 参照）")


def main():
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    title, body = load_article()

    with sync_playwright() as p:
        print("ブラウザ起動中...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("ログイン中...")
        page.goto("https://note.com/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.fill("input[type='email'], input[id='email']", EMAIL)
        page.wait_for_timeout(300)
        page.fill("input[type='password']", PASSWORD)
        page.wait_for_timeout(300)
        page.click("button[type='submit'], button:has-text('ログイン')")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)
        print("ログイン完了:", page.url)

        print("記事作成ページへ移動...")
        page.goto("https://note.com/notes/new", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        print("タイトル入力中...")
        title_sel = "textarea, input[placeholder*='タイトル'], [data-placeholder*='タイトル']"
        page.wait_for_selector(title_sel, timeout=10000)
        page.fill(title_sel, title)
        page.wait_for_timeout(800)

        page.keyboard.press("Tab")
        page.wait_for_timeout(500)

        print("本文入力中...")
        type_article(page, body)
        page.wait_for_timeout(1000)

        print("サムネイルアップロード中...")
        upload_thumbnail(page, THUMBNAIL)

        print("下書き保存中...")
        try:
            page.click("button:has-text('下書き保存')", timeout=5000)
        except PWTimeout:
            try:
                page.click("button:has-text('保存')", timeout=3000)
            except PWTimeout:
                page.keyboard.press("Control+s")
        page.wait_for_timeout(3000)

        print("\n完了！下書き保存しました")
        print(f"URL: {page.url}")
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
    input("Enterキーで終了...")
