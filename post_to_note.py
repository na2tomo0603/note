#!/usr/bin/env python3
import sys
import traceback
import requests

EMAIL    = "na2tomo0603@gmail.com"
PASSWORD = "ymas0603"
USER_ID  = "na2tomo0603"

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

Claude Codeは「AIがコードを書く」ツールではなく、「人間とAIが協働する」ための道具だと思う。うまく活用することで、開発のスピードと品質を同時に上げられる可能性がある。まだ試したことがない方は、ぜひ一度体験してみてほしい。"""


def login(session):
    # ログインページを先に取得してCookieをセット
    session.get("https://note.com/login")

    endpoints = [
        ("POST", "https://note.com/api/v1/sessions",  {"login": EMAIL, "password": PASSWORD}),
        ("POST", "https://note.com/api/v2/sessions",  {"login": EMAIL, "password": PASSWORD}),
        ("POST", "https://note.com/api/v1/sessions",  {"email": EMAIL, "password": PASSWORD}),
        ("POST", "https://note.com/api/v3/sessions",  {"login": EMAIL, "password": PASSWORD}),
    ]

    for method, url, payload in endpoints:
        print(f"Trying {url} ...")
        res = session.post(url, json=payload)
        print(f"  -> {res.status_code}: {res.text[:120]}")
        if res.status_code in (200, 201):
            data = res.json().get("data", {})
            token = data.get("token")
            if token:
                session.headers["X-Note-Token"] = token
            print("Login OK")
            return True
    return False


def main():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Referer": "https://note.com/",
        "Origin": "https://note.com",
    })

    print("Logging in to note.com...")
    if not login(session):
        print("All login attempts failed.")
        sys.exit(1)

    print("Creating draft...")
    res2 = session.post(
        "https://note.com/api/v1/text_notes",
        json={"name": TITLE, "body": BODY, "status": "draft"},
    )
    print(f"Draft status: {res2.status_code}")
    print(res2.text[:500])

    if res2.status_code in (200, 201):
        note_key = res2.json().get("data", {}).get("key", "")
        print()
        print("SUCCESS! Draft saved.")
        print(f"URL: https://note.com/{USER_ID}/n/{note_key}")
    else:
        print("Draft creation failed.")
        sys.exit(1)


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
