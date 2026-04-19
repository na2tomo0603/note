# Creema クロスポストスキル

Creemaの商品URLを受け取り、商品情報（タイトル・価格・説明文・画像）を自動取得して、他のハンドメイド販売サイトに下書き投稿します。

## 対応投稿先

| サイト | キーワード |
|--------|-----------|
| minne  | `minne`（省略時のデフォルト） |
| iichi  | `iichi` |

## 使い方

```
/creema-cross-post https://www.creema.jp/item/XXXXXXX [投稿先]
```

例:
```
/creema-cross-post https://www.creema.jp/item/1234567 minne
/creema-cross-post https://www.creema.jp/item/1234567 iichi
```

## 事前設定

初回利用前に `creema_cross_post.py` 上部の認証情報を設定してください。
環境変数でも設定できます:

```bash
export MINNE_EMAIL="your@email.com"
export MINNE_PASSWORD="yourpassword"
export IICHI_EMAIL="your@email.com"
export IICHI_PASSWORD="yourpassword"
```

## 実行手順

引数としてCreemaのURLと投稿先が渡されたら、以下を順番に実行してください。

### ステップ1: 認証情報の確認

`creema_cross_post.py` の認証情報設定（MINNE_EMAIL等）が `your_*` のままであれば、
ユーザーに認証情報の設定を促してください。

### ステップ2: クロスポスト実行

```bash
python3 creema_cross_post.py "$ARGUMENTS"
```

`$ARGUMENTS` には「CreemaURL [投稿先]」が入ります。

### ステップ3: 結果確認

スクリプト実行後、以下のファイルが生成されます:
- `creema_product.json` — 取得した商品情報（JSON）
- `creema_images/` — ダウンロードした商品画像

### ステップ4: 完了報告

以下を報告してください:
- 取得した商品タイトル・価格
- 投稿先サイトと結果URL（成功/失敗）
- 失敗した場合は `error.log` の内容

## トラブルシューティング

- **ログイン失敗**: 認証情報を確認してください
- **セレクター不一致**: サイトのHTML構造が変わった可能性があります。`error.log` を確認してください
- **画像アップロード失敗**: 投稿後に手動で画像を追加してください
