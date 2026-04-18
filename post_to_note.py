#!/usr/bin/env python3
import sys
import re
import os
import traceback

EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"
USER_ID  = "na2tomo0603"

TITLE = "シニア世代がSNS不要でnoteを収益化できる理由【副業・在宅ワーク】"

BODY = """\
「副業を始めたいけど、SNSは難しそう…」
「XやInstagramを毎日更新するなんて、体力的にも気力的にも無理」

そう感じているシニア世代の方は多いのではないでしょうか。

実は、noteはSNSのフォロワーがゼロでも収益化できる、シニアにとって理想に近いプラットフォームです。今回は「なぜnote一択なのか」をわかりやすくお伝えします。

## なぜnoteはSNS不要なのか

一般的な副業では「まずSNSでフォロワーを増やして…」という流れが当たり前です。しかしnoteは違います。

noteに書いた記事は、note内の検索とGoogle検索の両方から読んでもらえます。つまり、毎日投稿しなくても、バズらなくても、フォロワーがゼロでも——あなたの記事が誰かの悩みを解決すれば、それがそのまま収益につながる仕組みです。

これがnoteを「働かない働き方」と呼ぶ理由です。一度書いた記事は半永久的にインターネット上に残り、寝ている間も読まれ続けます。

## シニア世代こそnoteが向いている3つの理由

60代・70代の方が持つ「仕事で培ったノウハウ」「子育ての経験」「趣味の深い知識」は、若い世代には絶対に書けない価値ある情報です。

「定年後の手続きで困ったこと」「年金との付き合い方」「50年続けた料理のコツ」——こういった内容こそ、同世代の読者が「まさに知りたかった！」と感じるコンテンツです。

またSNSと違い、noteは週1回でも月1回でも構いません。自分のペースで書けるのは、体力や時間に制約があるシニアにとって大きなメリットです。

## noteの収益化　3つの方法

有料記事の販売では、500円〜の記事に値段をつけて販売できます。手数料は約15%。フォロワーゼロでも、検索で見つけてもらえれば売れます。

2024年から始まったAI学習対価還元プログラムでは、無料記事を書くだけでAI企業への学習データとして対価が支払われます。一般ユーザーでも数万円〜の収益を得た事例があります。

メンバーシップ（月額サブスク）では、固定のファンができてきたら月額制のコンテンツを提供できます。少人数でも安定収益になります。

## まず1記事、書いてみよう

難しく考える必要はありません。あなたが「当たり前」と思っていることが、誰かにとっては貴重な情報です。

まずは1000文字、自分の経験を書いてみてください。それが「働かない働き方」への第一歩になります。

SNSが苦手なシニア世代にとって、noteは最も始めやすく、最も続けやすい収益化の手段です。"""

TAGS = ["副業", "在宅ワーク", "シニア", "note収益化", "副業初心者", "働かない働き方", "60代副業", "SNS不要"]
THUMBNAIL = "thumbnail.png"


def insert_text(page, text):
    """JavaScript execCommand でエディタに直接テキスト挿入（長さ制限なし）"""
    # 改行を含むテキストを安全に渡すためJSONエンコード
    import json
    js = f"document.execCommand('insertText', false, {json.dumps(text)})"
    page.evaluate(js)
    page.wait_for_timeout(100)


def type_article(page, body):
    """見出し・本文を入力。見出しはキー操作、段落はexecCommandで直接挿入"""
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("## "):
            # H2見出し: ## + スペース でnote.comが自動変換
            page.keyboard.type("## ")
            page.wait_for_timeout(200)
            insert_text(page, line[3:])
            page.keyboard.press("Enter")
            page.wait_for_timeout(300)

        elif line.strip() == "":
            page.keyboard.press("Enter")
            page.wait_for_timeout(100)

        else:
            # 段落をまとめてexecCommandで一括挿入
            para_lines = []
            while i < len(lines) and lines[i].strip() != "" and not lines[i].startswith("## "):
                para_lines.append(lines[i])
                i += 1
            insert_text(page, "\n".join(para_lines))
            page.keyboard.press("Enter")
            page.keyboard.press("Enter")
            page.wait_for_timeout(200)
            continue

        i += 1


def upload_thumbnail(page, thumbnail_path):
    """カバー画像をアップロード"""
    if not os.path.exists(thumbnail_path):
        print("thumbnail.png が見つかりません。スキップします")
        return

    abs_path = os.path.abspath(thumbnail_path)

    # 現在の画面をスクショ保存して確認
    page.screenshot(path="screen_before_thumb.png")
    print("スクリーンショット保存: screen_before_thumb.png")

    # すべてのfile inputに直接セット（クリック不要）
    file_inputs = page.locator("input[type='file']")
    count = file_inputs.count()
    print(f"ファイル入力欄: {count}個見つかりました")

    if count > 0:
        try:
            file_inputs.first.set_input_files(abs_path)
            page.wait_for_timeout(3000)
            page.screenshot(path="screen_after_thumb.png")
            print("サムネイルアップロード完了")
            return
        except Exception as e:
            print(f"直接セット失敗: {e}")

    # file inputが非表示の場合、ボタンクリック→ダイアログ捕捉
    try:
        with page.expect_file_chooser(timeout=6000) as fc_info:
            for sel in [
                "button:has-text('カバー')",
                "button:has-text('画像')",
                "[class*='cover'] button",
                "[class*='thumbnail'] button",
            ]:
                try:
                    page.click(sel, timeout=2000)
                    break
                except Exception:
                    continue
        fc_info.value.set_files(abs_path)
        page.wait_for_timeout(3000)
        print("サムネイルアップロード完了")
    except Exception as e:
        print(f"サムネイルアップロード失敗: {e}")
        print("→ screen_before_thumb.png を確認して手動でカバー画像を設定してください")


def main():
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        print("ブラウザ起動中...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # ログイン
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

        # 記事作成ページ
        print("記事作成ページへ移動...")
        page.goto("https://note.com/notes/new", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # タイトル入力
        print("タイトル入力中...")
        title_sel = "textarea, input[placeholder*='タイトル'], [data-placeholder*='タイトル']"
        page.wait_for_selector(title_sel, timeout=10000)
        page.fill(title_sel, TITLE)
        page.wait_for_timeout(800)

        # 本文エリアへ移動
        page.keyboard.press("Tab")
        page.wait_for_timeout(500)

        # 本文入力（見出し対応＋クリップボード貼り付け）
        print("本文入力中...")
        type_article(page, BODY)
        page.wait_for_timeout(1000)

        # サムネイルアップロード
        print("サムネイルアップロード中...")
        upload_thumbnail(page, THUMBNAIL)

        # 下書き保存
        print("下書き保存中...")
        try:
            page.click("button:has-text('下書き保存')", timeout=5000)
        except PWTimeout:
            try:
                page.click("button:has-text('保存')", timeout=3000)
            except PWTimeout:
                page.keyboard.press("Control+s")
        page.wait_for_timeout(3000)

        print()
        print("完了！下書き保存しました")
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
