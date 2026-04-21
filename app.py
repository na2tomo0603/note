#!/usr/bin/env python3
"""
Creema → Minne 自動登録アプリ
Flask APIサーバー（iPhone対応PWA）
"""

import os
import json
import threading
import traceback
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

# 進捗ログ
_progress = []
_progress_lock = threading.Lock()


def log(msg):
    print(msg, flush=True)
    with _progress_lock:
        _progress.append(str(msg))


def clear_progress():
    with _progress_lock:
        _progress.clear()


def get_progress():
    with _progress_lock:
        return list(_progress)


# ── 静的ファイル ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


# ── API ──────────────────────────────────────────────────────────────────────

@app.route("/api/progress")
def progress():
    return jsonify({"logs": get_progress()})


@app.route("/api/scrape", methods=["POST"])
def scrape():
    """Creema URLから商品情報を取得"""
    data = request.get_json(force=True) or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"ok": False, "error": "URLを入力してください"}), 400
    if "creema.jp" not in url:
        return jsonify({"ok": False, "error": "CreemaのURLを入力してください"}), 400

    clear_progress()
    try:
        from creema_scraper import scrape as do_scrape, download_images
        product = do_scrape(url, log=log)
        log("画像をダウンロード中...")
        img_paths = download_images(product, save_dir="tmp_images", log=log)
        log(f"画像ダウンロード完了: {len(img_paths)}枚")

        result = product.to_dict()
        result["image_paths"] = img_paths

        # セッション保存
        with open("product_cache.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        log("取得完了！")
        return jsonify({"ok": True, "product": result})

    except Exception:
        msg = traceback.format_exc()
        log(msg)
        return jsonify({"ok": False, "error": msg}), 500


@app.route("/api/product", methods=["GET"])
def get_product():
    """キャッシュされた商品情報を返す"""
    try:
        with open("product_cache.json", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"ok": True, "product": data})
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "商品情報がありません"})


@app.route("/api/product", methods=["PUT"])
def update_product():
    """商品情報を編集して保存"""
    data = request.get_json(force=True) or {}
    try:
        with open("product_cache.json", encoding="utf-8") as f:
            existing = json.load(f)
        existing.update({k: v for k, v in data.items() if k != "image_paths"})
        with open("product_cache.json", "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/post", methods=["POST"])
def post():
    """Minneに商品を登録する"""
    data = request.get_json(force=True) or {}
    clear_progress()

    try:
        with open("product_cache.json", encoding="utf-8") as f:
            product = json.load(f)
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "先にCreemaから商品を取得してください"}), 400

    # 認証情報をマージ（リクエストになければ保存済み設定から読む）
    try:
        with open("settings.json", encoding="utf-8") as f:
            saved = json.load(f)
    except FileNotFoundError:
        saved = {}
    product["_minne_email"]    = data.get("email", "")    or saved.get("email", "")
    product["_minne_password"] = data.get("password", "") or saved.get("password", "")

    image_paths = product.get("image_paths", [])

    try:
        from minne_poster import post_product
        result_url = post_product(product, image_paths, log=log, headless=True)
        log(f"Minne登録完了: {result_url}")
        return jsonify({"ok": True, "url": result_url})
    except Exception:
        msg = traceback.format_exc()
        log(msg)
        return jsonify({"ok": False, "error": msg}), 500


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """保存済み設定を返す（パスワードは除く）"""
    try:
        with open("settings.json", encoding="utf-8") as f:
            s = json.load(f)
        s.pop("password", None)
        return jsonify({"ok": True, "settings": s})
    except FileNotFoundError:
        return jsonify({"ok": True, "settings": {}})


@app.route("/api/settings", methods=["PUT"])
def save_settings():
    """メールアドレス等を保存"""
    data = request.get_json(force=True) or {}
    try:
        try:
            with open("settings.json", encoding="utf-8") as f:
                existing = json.load(f)
        except FileNotFoundError:
            existing = {}
        existing.update(data)
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"サーバー起動: http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
