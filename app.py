#!/usr/bin/env python3
"""
iPhone対応PWA - YouTube → note.com 自動投稿アプリ
Flask APIサーバー
"""

import os
import re
import sys
import json
import threading
import traceback
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

# 進捗ログをメモリに保持
_progress = []
_progress_lock = threading.Lock()


def log(msg):
    print(msg, flush=True)
    with _progress_lock:
        _progress.append(msg)


def clear_progress():
    with _progress_lock:
        _progress.clear()


def get_progress():
    with _progress_lock:
        return list(_progress)


# ─── API エンドポイント ───────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/process", methods=["POST"])
def process():
    """YouTube URL → 記事生成 → article_draft.md 保存"""
    data = request.get_json(force=True)
    url = (data or {}).get("url", "").strip()
    if not url:
        return jsonify({"ok": False, "error": "URLを入力してください"}), 400

    clear_progress()

    try:
        from youtube_to_note import (
            get_video_id, get_transcript, get_video_title,
            format_article_with_claude, make_thumbnail, save_article,
        )

        log("動画IDを解析中...")
        video_id = get_video_id(url)
        log(f"動画ID: {video_id}")

        log("字幕を取得中...")
        raw_text = get_transcript(video_id)
        log(f"字幕取得完了: {len(raw_text)}文字")

        log("タイトルを取得中...")
        video_title = get_video_title(video_id)
        log(f"タイトル: {video_title}")

        log("Claude APIで記事を生成中...")
        result = format_article_with_claude(raw_text, video_title)
        body, title, tags = result if len(result) == 3 else (result[0], video_title, "")
        log(f"記事生成完了: {len(body)}文字")

        log("サムネイルを生成中...")
        make_thumbnail(title)

        log("article_draft.md を保存中...")
        save_article(title, body, tags)
        log("完了！")

        with open("article_draft.md", encoding="utf-8") as f:
            draft = f.read()

        return jsonify({"ok": True, "title": title, "tags": tags, "body": body, "draft": draft})

    except SystemExit as e:
        msg = f"処理中断: {e}"
        log(msg)
        return jsonify({"ok": False, "error": msg}), 500
    except Exception:
        msg = traceback.format_exc()
        log(msg)
        return jsonify({"ok": False, "error": msg}), 500


@app.route("/api/progress")
def progress():
    """現在の進捗ログを返す"""
    return jsonify({"logs": get_progress()})


@app.route("/api/article")
def get_article():
    """article_draft.md を返す"""
    try:
        with open("article_draft.md", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        title = lines[0].lstrip("# ").strip() if lines else ""
        body = "\n".join(lines[1:]).strip()
        return jsonify({"ok": True, "title": title, "body": body, "raw": content})
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "article_draft.md が見つかりません"})


@app.route("/api/article", methods=["PUT"])
def update_article():
    """記事を編集して保存"""
    data = request.get_json(force=True) or {}
    title = data.get("title", "下書き")
    body = data.get("body", "")
    tags = data.get("tags", "")

    from youtube_to_note import save_article
    save_article(title, body, tags)
    return jsonify({"ok": True})


@app.route("/api/post", methods=["POST"])
def post_article():
    """note.com に下書き投稿"""
    clear_progress()
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "post_to_note.py"],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout + result.stderr
        for line in output.splitlines():
            log(line)

        if result.returncode == 0:
            return jsonify({"ok": True, "output": output})
        else:
            return jsonify({"ok": False, "error": output}), 500
    except Exception:
        msg = traceback.format_exc()
        log(msg)
        return jsonify({"ok": False, "error": msg}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"サーバー起動: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
