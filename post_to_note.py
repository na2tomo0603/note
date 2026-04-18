#!/usr/bin/env python3
"""
note.com 下書き自動投稿スクリプト
参考: https://note.com/hirosuke_0520/n/n8ed734a89ee6

【使い方】
1. pip install noteclient
2. python3 post_to_note.py

【必要環境】
- Firefox がインストールされていること
- geckodriver が PATH に入っていること
  - Mac: brew install geckodriver
  - Windows: https://github.com/mozilla/geckodriver/releases
"""

import sys
import traceback
from note_client.note_client import Note

EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"
USER_ID  = "na2tomo0603"   # note.com のユーザーID (URLの /ユーザーID/ 部分)

TITLE = "AIと共に働く時代へ――Claude Codeを使ってみた"

BODY = """\
最近、開発の現場でAIツールを活用する機会が増えてきた。なかでも注目しているのが、Anthropicが提供する「Claude Code」だ。ターミナル上で動作するAIアシスタントで、コードの生成・修正から、ファイル操作、GitHubとの連携まで、幅広い作業をこなしてくれる。今回は実際に使ってみた感想をまとめてみたい。

## 使ってみて感じたこと

まず驚いたのは、自然言語で指示するだけで、複数のファイルにまたがる変更を一気にやってくれる点だ。「この関数をリファクタリングして」「テストを追加して」といった曖昧な指示でも、文脈を読み取りながら的確に動いてくれる。プロジェクトの構造を把握した上で、最適なアプローチを選んでくれるのは頼もしい。

また、コードを書くだけでなく、「なぜこう実装するのか」を説明してくれるのも助かる。ジュニアエンジニアにとっては、経験豊富なメンターと一緒に作業している感覚に近いかもしれない。チームの生産性向上だけでなく、個人のスキルアップにもつながりそうだ。

実際の業務では、バグ修正やコードレビューの補助として使うことが多い。「このエラーの原因を調べて」と投げかけると、ログを解析して原因箇所を特定し、修正案まで提示してくれる。これまで30分かかっていた作業が5分で終わることもあり、体感できる効率化は大きい。

## 気をつけたいこと

もちろん、AIが生成したコードをそのまま使うのは危険だ。セキュリティの観点から、出力を必ずレビューする習慣が重要になる。また、複雑なドメイン知識が必要な場面では、まだ人間の判断が不可欠だと感じた。AIを「自動化ツール」ではなく「優秀なアシスタント」として扱うことが、うまく付き合うコツだと思う。

## まとめ

Claude Codeは「AIがコードを書く」ツールではなく、「人間とAIが協働する」ための道具だと思う。うまく活用することで、開発のスピードと品質を同時に上げられる可能性がある。まだ試したことがない方は、ぜひ一度体験してみてほしい。\
"""

TAGS = ["AI", "ClaudeCode", "生成AI", "プログラミング"]


def main():
    print("note.com へ下書き投稿を開始します...")
    print(f"  タイトル: {TITLE}")
    print(f"  ユーザー: {USER_ID}")
    print()

    note = Note(email=EMAIL, password=PASSWORD, user_id=USER_ID)

    result = note.create_article(
        title=TITLE,
        input_tag_list=TAGS,
        image_index=None,   # サムネイル画像なし
        post_setting=False, # False=下書き保存 / True=公開
        text=BODY,
        headless=True,      # ブラウザを非表示で実行
    )

    if result.get("run") == "success":
        print("✅ 下書き保存に成功しました！")
        print(f"  設定: {result.get('post_setting')}")
        print(f"  タグ: {result.get('tag_list')}")
        if result.get("post_url"):
            print(f"  URL: {result.get('post_url')}")
    else:
        print("❌ 投稿に失敗しました")
        print(result)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = traceback.format_exc()
        print("ERROR:", msg)
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(msg)
        print("error.log に保存しました。そのファイルの中身を教えてください。")
    input("Enterキーを押して終了...")
