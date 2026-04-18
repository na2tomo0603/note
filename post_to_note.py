#!/usr/bin/env python3
import sys
import traceback

EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"

TITLE = "AIと共に働く時代へ――Claude Codeを使ってみた"

BODY = """\
最近、開発の現場でAIツールを活用する機会が増えてきた。なかでも注目しているのが、Anthropicが提供する「Claude Code」だ。ターミナル上で動作するAIアシスタントで、コードの生成・修正から、ファイル操作、GitHubとの連携まで、幅広い作業をこなしてくれる。今回は実際に使ってみた感想をまとめてみたい。

使ってみて感じたこと

まず驚いたのは、自然言語で指示するだけで、複数のファイルにまたがる変更を一気にやってくれる点だ。「この関数をリファクタリングして」「テストを追加して」といった曖昧な指示でも、文脈を読み取りながら的確に動いてくれる。プロジェクトの構造を把握した上で、最適なアプローチを選んでくれるのは頼もしい。

また、コードを書くだけでなく、「なぜこう実装するのか」を説明してくれるのも助かる。ジュニアエンジニアにとっては、経験豊富なメンターと一緒に作業している感覚に近いかもしれない。チームの生産性向上だけでなく、個人のスキルアップにもつながりそうだ。

実際の業務では、バグ修正やコードレビューの補助として使うことが多い。「このエラーの原因を調べて」と投げかけると、ログを解析して原因箇所を特定し、修正案まで提示してくれる。これまで30分かかっていた作業が5分で終わることもあり、体感できる効率化は大きい。

気をつけたいこと

もちろん、AIが生成したコードをそのまま使うのは危険だ。セキュリティの観点から、出力を必ずレビューする習慣が重要になる。また、複雑なドメイン知識が必要な場面では、まだ人間の判断が不可欠だと感じた。AIを「自動化ツール」ではなく「優秀なアシスタント」として扱うことが、うまく付き合うコツだと思う。

まとめ

Claude Codeは「AIがコードを書く」ツールではなく、「人間とAIが協働する」ための道具だと思う。うまく活用することで、開発のスピードと品質を同時に上げられる可能性がある。まだ試したことがない方は、ぜひ一度体験してみてほしい。"""


def main():
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        print("Starting browser...")
        browser = p.chromium.launch(headless=False)  # headless=False で画面表示
        page = browser.new_page()

        # ログイン
        print("Opening note.com login page...")
        page.goto("https://note.com/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        print("Filling in credentials...")
        page.fill("input[type='email'], input[id='email'], input[name='email']", EMAIL)
        page.wait_for_timeout(500)
        page.fill("input[type='password']", PASSWORD)
        page.wait_for_timeout(500)

        print("Clicking login button...")
        page.click("button[type='submit'], button:has-text('ログイン')")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)
        print(f"Logged in. URL: {page.url}")

        # 新規記事作成ページへ
        print("Opening new article page...")
        page.goto("https://note.com/notes/new", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # タイトル入力
        print("Entering title...")
        title_sel = "textarea, input[placeholder*='タイトル'], [data-placeholder*='タイトル']"
        page.wait_for_selector(title_sel, timeout=10000)
        page.click(title_sel)
        page.keyboard.type(TITLE)
        page.wait_for_timeout(500)

        # 本文入力
        print("Entering body...")
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)
        page.keyboard.type(BODY)
        page.wait_for_timeout(1000)

        # 下書き保存
        print("Saving draft...")
        try:
            page.click("button:has-text('下書き保存'), button:has-text('保存')", timeout=5000)
        except PWTimeout:
            # キーボードショートカットで保存を試みる
            page.keyboard.press("Control+s")
        page.wait_for_timeout(3000)

        print()
        print("SUCCESS! Draft saved.")
        print(f"Current URL: {page.url}")

        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        msg = traceback.format_exc()
        print("ERROR:", msg)
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(msg)
        print("Saved to error.log")
    input("Press Enter to exit...")
