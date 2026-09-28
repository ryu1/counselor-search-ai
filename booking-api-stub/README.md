# booking-api-stub

カウンセリング予約APIのスタブ実装。FastAPI + SQLModel + SQLite + Zappa。

## 概要

- **エンドポイント**: `POST /bookings` - 予約登録のみ
- **データ保存**: SQLModel経由でSQLite (`tmp/booking.db`) に保存
- **デプロイ**: ZappaでAWS Lambda + API Gatewayへデプロイ可能
- **注意**: Lambda上ではSQLiteの永続性が保証されないため、スタブ用途のみ

## セットアップ

```bash
cd booking-api-stub

# 依存関係インストール（開発用含む）
uv sync --extra dev
```

## ローカル開発

### APIサーバー起動

```bash
uv run fastapi dev booking_api/main.py
```

- http://localhost:8000 で起動
- http://localhost:8000/docs でSwagger UI確認可能

### APIテスト例

```bash
curl -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "name": "田中太郎",
    "email": "tanaka@example.com",
    "booking_datetime": "2026-10-01T10:00:00",
    "consultation_content": "仕事のストレスについて相談したい",
    "counseling_office_name": "東京カウンセリングオフィス"
  }'
```

正常時のレスポンス (201 Created):

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

## テスト実行

```bash
# 全テスト実行
PYTHONPATH=. uv run pytest -v

# カバレッジ付き
PYTHONPATH=. uv run pytest -v --cov=booking_api
```

### テスト内容

- 正常な予約登録（201返却、DB保存確認）
- 必須パラメータ不足（422返却）
- 不正なメールアドレス形式（422返却）
- 不正な日時形式（422返却）
- 空文字・文字数超過のバリデーション（422返却）

## コード品質チェック

```bash
# リント
uv run ruff check booking_api/

# フォーマット
uv run ruff format booking_api/

# 型チェック
uv run pyright booking_api/
```

## デプロイ (AWS Lambda + API Gateway)

### 前提条件

- AWS CLI設定済み (`aws configure` / `aws configure sso`)
- S3バケット作成済み（`zappa_settings.json` の `s3_bucket` に指定）

```bash
# S3バケット作成例
aws s3 mb s3://counselor-search-ai-zappa-deploy --region ap-northeast-1
```

### 初回デプロイ

```bash
uv run zappa deploy dev
```

デプロイ成功後、API GatewayのURLが表示されます。

### コード更新時

```bash
uv run zappa update dev
```

### ログ確認

```bash
uv run zappa tail dev
```

### 削除

```bash
uv run zappa undeploy dev
```

## Zappa設定の注意点

- `app_type: "asgi"` - FastAPIはASGIアプリのため必須
- `app_function: "booking_api.main.app"` - エントリーポイント
- `slim_handler: true` - パッケージサイズ対策（依存関係をS3から読み込み）
- Lambdaでは `/tmp` のみ書き込み可能。冷間起動時にDBが消える可能性あり（スタブ用途として許容）

## プロジェクト構成

```
booking-api-stub/
├── pyproject.toml           # uvプロジェクト設定
├── uv.lock                  # ロックファイル
├── zappa_settings.json      # Zappaデプロイ設定
├── README.md                # このファイル
├── booking_api/
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

### POST /bookings

予約を登録する。

#### リクエストボディ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| name | string | ✓ | 予約者名（1-100文字） |
| email | string | ✓ | メールアドレス（メール形式） |
| booking_datetime | string | ✓ | 予約日時（ISO 8601形式） |
| consultation_content | string | ✓ | 相談内容（1文字以上） |
| counseling_office_name | string | ✓ | カウンセリングオフィス名（1-200文字） |

#### レスポンス (201 Created)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | integer | 自動採番ID |
| name | string | 予約者名 |
| email | string | メールアドレス |
| booking_datetime | string | 予約日時（ISO 8601） |
| consultation_content | string | 相談内容 |
| counseling_office_name | string | オフィス名 |
| created_at | string | 登録日時（ISO 8601） |

#### エラーレスポンス (422 Unprocessable Entity)

FastAPI標準のバリデーションエラー形式で返却される。

## ライセンス

個人利用・学習目的のデモプロジェクトです。