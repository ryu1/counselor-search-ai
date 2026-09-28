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

## デプロイ

### AWS Lambda + API Gateway (Zappa)

```bash
# S3バケット作成
aws s3 mb s3://counselor-search-ai-zappa-deploy --region ap-northeast-1

# デプロイ
uv run zappa deploy dev

# 更新
uv run zappa update dev

# ログ確認
uv run zappa tail dev

# 削除
uv run zappa undeploy dev
```

### 環境変数

| 変数 | デフォルト値 | 説明 |
|------|-------------|------|
| DATABASE_URL | `sqlite:///./tmp/booking.db` | SQLite接続URL |
| ENVIRONMENT | `dev` | 環境名 |

## ローカル開発

```bash
# 依存関係インストール
uv sync --extra dev

# 開発サーバー起動
uv run fastapi dev src/booking_api/main.py

# テスト実行
PYTHONPATH=. uv run pytest -v

# コード品質チェック
uv run ruff check src/
uv run ruff format src/ --check
uv run pyright src/
```

## 技術スタック

| カテゴリ | 技術 | バージョン |
|----------|------|------------|
| フレームワーク | FastAPI | 0.110+ |
| ORM | SQLModel | 0.0.22+ |
| DB | SQLite | - |
| ASGIサーバー | Uvicorn | 0.29+ |
| デプロイ | Zappa | 0.60+ |
| Python | - | 3.11+ |
| パッケージ管理 | uv | - |

## Zappa設定のポイント

```json
{
  "dev": {
    "app_function": "booking_api.main.app",
    "app_type": "asgi",
    "s3_bucket": "counselor-search-ai-zappa-deploy",
    "project_name": "booking-api-stub",
    "runtime": "python3.11",
    "region": "ap-northeast-1",
    "memory_size": 256,
    "timeout_seconds": 30,
    "slim_handler": true,
    "cors_options": {
      "allowedOrigins": ["*"],
      "allowedMethods": ["GET", "POST", "OPTIONS"],
      "allowedHeaders": ["Content-Type", "Authorization"]
    },
    "environment_variables": {
      "DATABASE_URL": "sqlite:///./tmp/booking.db",
      "ENVIRONMENT": "dev"
    }
  }
}
```

### 重要な設定

| 設定 | 値 | 理由 |
|------|-----|------|
| `app_type: "asgi"` | 必須 | FastAPIはASGIアプリのため |
| `slim_handler: true` | 推奨 | パッケージサイズ削減（50MB制限対策） |
| `app_function` | `booking_api.main.app` | エントリーポイント |

## 注意事項

- **SQLiteの永続性**: Lambdaでは `/tmp` のみ書き込み可能。冷間起動時にDBが消える可能性あり（スタブ用途として許容）
- **Zappa ASGI制約**: lifespan protocol非対応、`startup`/`shutdown` イベント使用不可
- **API Gatewayタイムアウト**: 30秒制限
- **パッケージサイズ**: 50MB制限（`slim_handler`で対応）

## 関連ドキュメント

- [README.md](../booking-api-stub/README.md) - 詳細な手順書
- [architecture.md](architecture.md) - システム全体構成
- [lambda-deployment.md](lambda-deployment.md) - Lambdaデプロイ手順