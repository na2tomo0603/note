# note.com 下書き投稿スキル

`article_draft.md` の内容をPlaywrightでnote.comに下書き投稿します。

## 手順

1. `article_draft.md` を読み込む
2. タイトルと本文を抽出する
3. `post_to_note.py` を実行して下書きをnote.comに保存する

## 実行

```bash
python post_to_note.py
```

## 注意事項

- Playwrightのブラウザ操作でnote.comにログインして投稿します
- サムネイル（`thumbnail.png`）が存在すれば自動アップロードを試みます
- 失敗した場合は手動でカバー画像を設定してください
- 投稿後のURLをユーザーに報告してください
