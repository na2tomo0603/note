#!/usr/bin/env python3
"""note.com に下書き記事を投稿するスクリプト（ローカルPC用）"""

import requests
import json
import sys

EMAIL = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"

TITLE = "AIと共に働く時代へ――Claude Codeを使ってみた"
BODY = """最近、開発の現場でAIツールを活用する機会が増えてきた。なかでも注目しているのが、Anthropicが提供する「Claude Code」だ。ターミナル上で動作するAIアシスタントで、コードの生成・修正から、ファイル操作、GitHubとの連携まで、幅広い作業をこなしてくれる。今回は実際に使ってみた感想をまとめてみたい。

使ってみて感じたこと

まず驚いたのは、自然言語で指示するだけで、複数のファイルにまたがる変更を一気にやってくれる点だ。「この関数をリファクタリングして」「テストを追加して」といった曖昧な指示でも、文脈を読み取りながら的確に動いてくれる。プロジェクトの構造を把握した上で、最適なアプローチを選んでくれるのは頼もしい。

また、コードを書くだけでなく、「なぜこう実装するのか」を説明してくれるのも助かる。ジュニアエンジニアにとっては、経験豊富なメンターと一緒に作業している感覚に近いかもしれない。チームの生産性向上だけでなく、個人のスキルアップにもつながりそうだ。

実際の業務では、バグ修正やコードレビューの補助として使うことが多い。「このエラーの原因を調べて」と投げかけると、ログを解析して原因箇所を特定し、修正案まで提示してくれる。これまで30分かかっていた作業が5分で終わることもあり、体感できる効率化は大きい。

気をつけたいこと

もちろん、AIが生成したコードをそのまま使うのは危険だ。セキュリティの観点から、出力を必ずレビューする習慣が重要になる。また、複雑なドメイン知識が必要な場面では、まだ人間の判断が不可欠だと感じた。AIを「自動化ツール」ではなく「優秀なアシスタント」として扱うことが、うまく付き合うコツだと思う。

まとめ

Claude Codeは「AIがコードを書く」ツールではなく、「人間とAIが協働する」ための道具だと思う。うまく活用することで、開発のスピードと品質を同時に上げられる可能性がある。まだ試したことがない方は、ぜひ一度体験してみてほしい。"""


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://note.com/",
        "Origin": "https://note.com",
    })

    # ログイン
    print("ログイン中...")
    login_res = session.post(
        "https://note.com/api/v1/sessions",
        json={"login": EMAIL, "password": PASSWORD},
    )
    print(f"ステータス: {login_res.status_code}")

    if login_res.status_code not in (200, 201):
        print("ログイン失敗:", login_res.text[:300])
        sys.exit(1)

    data = login_res.json()
    token = data.get("data", {}).get("token") or data.get("token")
    user_key = data.get("data", {}).get("urlname") or data.get("data", {}).get("id")
    print(f"ログイン成功: user={user_key}, token={str(token)[:20]}...")

    if token:
        session.headers["X-Note-Token"] = token

    # 下書き作成
    print("下書き作成中...")
    create_res = session.post(
        "https://note.com/api/v1/text_notes",
        json={
            "name": TITLE,
            "body": BODY,
            "status": "draft",
        },
    )
    print(f"作成ステータス: {create_res.status_code}")
    print(create_res.text[:500])

    if create_res.status_code in (200, 201):
        note_data = create_res.json()
        note_key = note_data.get("data", {}).get("key") or note_data.get("key")
        print(f"\n下書き保存完了！")
        print(f"URL: https://note.com/{user_key}/n/{note_key}")
    else:
        print("下書き作成失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
