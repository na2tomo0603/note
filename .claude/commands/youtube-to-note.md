# YouTube → note下書き自動投稿スキル

YouTubeのURLを受け取り、文字起こし→記事整形→サムネ生成→note.com下書き投稿まで自動で行います。

## 使い方

```
/youtube-to-note https://www.youtube.com/watch?v=XXXXXXXXX
```

## 実行手順

引数としてYouTube URLが渡されたら、以下を順番に実行してください。

### ステップ1: 字幕取得・記事生成・サムネ生成

```bash
python youtube_to_note.py "$ARGUMENTS"
```

### ステップ2: 結果確認

- `transcript.txt` に文字起こし結果が保存される
- `article_draft.md` に整形済み記事が保存される  
- `thumbnail.png` にサムネイルが生成される

### ステップ3: note.com に下書き投稿

```bash
python post_to_note.py
```

### ステップ4: 完了報告

投稿結果（成功/失敗）とnote.comのURLをユーザーに報告してください。
