# カウンセリング予約APIスタブ（booking-api-stub）

## 概要

カウンセリング予約情報を受け取り、SQLiteに保存するスタブAPI。
FastAPI + SQLModel + SQLite + Zappa で AWS Lambda + API Gateway にデプロイ。

## ディレクトリ構成

```
booking-api-stub/
├── pyproject.toml           # uvプロジェクト設定
├── uv.lock                  # ロックファイル
├── zappa_settings.json      # Zappaデプロイ設定
├── README.md                # 起動・テスト・デプロイ手順
├── src/booking_api/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリ・エンドポイント
│   ├── models.py            # SQLModel (テーブル + バリデーション)
│   └── database.py          # DB接続・セッション管理
├── tests/
│   ├── conftest.py          # pytestフィクスチャ
│   └── test_main.py         # APIエンドポイントテスト
└── tmp/
    └── booking.db           # SQLiteデータ（実行時に作成）
```

## API仕様

### エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/bookings` | 予約登録 |
| GET | `/health` | ヘルスチェック |

### POST /bookings

#### リクエストボディ

```json
{
  "name": "田中太郎",
  "email": "tanaka@example.com",
  "booking_datetime": "2026-10-01T10:00:00",
  "consultation_content": "仕事のストレスについて相談したい",
  "counseling_office_name": "東京カウンセリングオフィス"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| name | string | ✓ | 予約者名（1-100文字） |
| email | string | ✓ | メールアドレス（メール形式） |
| booking_datetime | string | ✓ | 予約日時（ISO 8601形式） |
| consultation_content | string | ✓ | 相談内容（1文字以上） |
| counseling_office_name | string | ✓ | カウンセリングオフィス名（1-200文字） |

#### レスポンス (201 Created)

```json
{
  "id": 1,
  "name": "田中太郎",
  "email": "tanaka@example.com",
  "booking_datetime": "2026-10-01T10:00:00",
  "consultation_content": "仕事のストレスについて相談したい",
  "counseling_office_name": "東京カウンセリングオフィス",
  "created_at": "2026-09-24T12:34:56.789012"
}
```

#### エラーレスポンス (422 Unprocessable Entity)

FastAPI標準のバリデーションエラー形式。

## 関連ドキュメント

- [README.md](../booking-api-stub/README.md) - 詳細な手順書（ローカル開発・テスト・デプロイ・品質チェック）
- [architecture.md](architecture.md) - システム全体構成・設計詳細
- [conventions.md](conventions.md) - デプロイ手順・クリーンアップ手順
- [lambda-deployment.md](lambda-deployment.md) - Lambdaデプロイ手順