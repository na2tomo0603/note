#!/usr/bin/env python3
import sys
import traceback

EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"

TITLE = "シニア世代がSNS不要でnoteを収益化できる理由"

BODY = """\
「副業を始めたいけど、SNSは難しそう…」「Xやインスタを毎日更新するなんて無理」と感じているシニア世代の方は多いのではないでしょうか。

実は、noteはSNSのフォロワーがゼロでも収益化できる唯一に近いプラットフォームです。今回は、その理由と具体的な始め方をお伝えします。

なぜnoteはSNS不要なのか

一般的な副業では「まずSNSでフォロワーを増やして…」という流れが当たり前です。しかしnoteは、記事をnote内の検索やGoogleからの検索で読んでもらえる仕組みになっています。

つまり、毎日投稿しなくても、バズらなくても、フォロワーがいなくても、あなたの記事が誰かの悩みを解決すれば、それがそのまま収益になります。

シニア世代こそnoteが向いている理由

人生経験がそのままコンテンツになる

60代・70代の方が持つ「仕事で培ったノウハウ」「子育ての経験」「趣味の深い知識」は、若い世代には絶対に書けない価値ある情報です。

「定年後の手続きで困ったこと」「年金との付き合い方」「50年続けた料理のコツ」―こういった内容こそ、同世代が読みたいと思うコンテンツです。

更新頻度のプレッシャーがない

SNSと違い、noteは週1回でも月1回でも構いません。一度書いた記事は半永久的にインターネット上に残り、読まれ続けます。まさに「働かない働き方」の仕組みです。

noteの収益化の仕組み

noteでの収益化には主に3つの方法があります。

① 有料記事の販売
500円〜の記事を販売します。手数料15%を引いた金額が振り込まれます。フォロワーゼロでも、検索で見つけてもらえれば売れます。

② AI学習対価還元プログラム（2024年〜）
無料記事を書くだけでAI企業への学習データとして対価が支払われる新制度です。一般ユーザーでも数万円〜の収益を得た事例があります。

③ メンバーシップ（月額サブスク）
固定ファンができたら月額制のコンテンツを提供できます。少人数でも安定収益に。

まず1記事書いてみよう

難しく考える必要はありません。あなたが「当たり前」と思っていることが、誰かにとっては貴重な情報です。

「定年後にやって良かったこと・後悔したこと」「趣味の〇〇を30年続けてわかったこと」「子育てを終えて気づいた、親として伝えたかったこと」

こんなテーマで、まず1000文字書いてみてください。SNSの知識もスマートフォンの特別なスキルも不要。パソコンで文字が打てれば、今日から始められます。

「難しそう」と思っていたnoteが、実はシニア世代にとって最も始めやすい収益化の手段かもしれません。"""


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
