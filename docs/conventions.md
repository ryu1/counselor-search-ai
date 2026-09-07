# 規約・手順書：カウンセラー検索AIデモ

## 目次

1. [ディレクトリ構成](#1-ディレクトリ構成)
2. [命名規則](#2-命名規則)
3. [コーディング規約](#3-コーディング規約)
4. [テスト規約](#4-テスト規約)
5. [Git規約](#5-git規約)
6. [セットアップ手順](#6-セットアップ手順)
7. [開発コマンド](#7-開発コマンド)
8. [CI/CD](#8-cicd)
9. [デプロイ手順](#9-デプロイ手順)

---

## 1. ディレクトリ構成

```
counselor-search-ai/
├── CLAUDE.md                    # AI参照ルール
├── AGENTS.md                    # プロジェクトメモリ
├── README.md                    # プロジェクト概要・ドキュメント目次
│
├── agent/                       # エージェント関連
│   ├── agentcore/               # AgentCore Runtime設定
│   │   ├── agentcore.json       # ランタイム定義
│   │   ├── aws-targets.json     # デプロイ先
│   │   ├── .env.local           # シークレット
│   │   ├── .gitignore           # 除外設定
│   │   └── cdk/                 # CDK プロジェクト
│   └── app/                     # エージェントコード
│       ├── app.py               # AgentCore Agent
│       ├── system-prompt.md     # システムプロンプト
│       ├── model/load.py        # モデルローダー
│       └── pyproject.toml       # Python依存関係
│
├── frontend/                    # Vue.js フロントエンド
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .env.local               # 環境変数 (VITE_API_URL)
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── styles/
│   │   │   └── global.css       # Tailwind ディレクティブ
│   │   ├── components/
│   │   │   ├── ChatView.vue
│   │   │   ├── MessageBubble.vue
│   │   │   └── InputArea.vue
│   │   └── stores/
│   │       └── chat.ts          # Pinia store
│   └── tests/
│       └── counselor-search.spec.ts  # E2Eテスト
│
├── backend/                     # Lambda検索Tool
│   ├── handler.py
│   ├── validator.py
│   ├── sql_builder.py
│   ├── aggregator.py
│   ├── models.py
│   └── proxy_handler.py         # AgentCoreプロキシLambda
│
└── docs/                        # 設計ドキュメント
    ├── product.md
    ├── architecture.md
    ├── design.md
    ├── api.md
    ├── tech.md
    ├── conventions.md
    ├── security.md
    ├── operations.md
    ├── review.md
    ├── glossary.md
    └── lambda-deployment.md
```

---

## 2. 命名規則

### 2.1 ファイル・ディレクトリ

| 対象 | ルール | 例 |
|------|--------|-----|
| Vueコンポーネント | PascalCase + `.vue` | `ChatView.vue` |
| TypeScriptモジュール | camelCase + `.ts` | `useChat.ts` |
| CSSモジュール | kebab-case + `.css` | `chat-view.css` |
| Pythonモジュール | snake_case + `.py` | `sql_builder.py` |
| データファイル | snake_case + `.jsonl` | `offices.jsonl` |
| ディレクトリ | kebab-case | `src/composables/` |

### 2.2 コード内の命名

| 対象 | ルール | 例 |
|------|--------|-----|
| Vueコンポーネント名 | PascalCase | `MessageBubble` |
| Vue prop名 | camelCase | `messageList` |
| Vue emit名 | camelCase | `sendMessage` |
| Pinia state | camelCase | `messageList`, `isLoading` |
| TypeScript関数 | camelCase | `validateConditions()` |
| TypeScriptインターフェース | PascalCase | `SearchConditions` |
| TypeScript列挙型 | PascalCase | `SearchStatus` |
| Python関数 | snake_case | `build_search_sql()` |
| Pythonクラス | PascalCase | `SearchConditions` |
| Python変数 | snake_case | `query_execution_id` |
| CloudFormationリソースID | PascalCase | `SearchCounselorsFunction` |
| Athenaテーブル名 | snake_case | `offices`, `counselors` |
| S3プレフィックス | snake_case | `offices/`, `counselors/` |

---

## 3. コーディング規約

### 3.1 フロントエンド (TypeScript / Vue)

**ESLint設定:**
```javascript
// eslint.config.js
import pluginVue from 'eslint-plugin-vue'
import vueTsEslintConfig from '@vue/eslint-config-typescript'

export default [
  ...pluginVue.configs['flat/essential'],
  ...vueTsEslintConfig(),
  {
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'off' // DOMPurifyでサニタイズ済み
    }
  }
]
```

**Prettier設定:**
```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2
}
```

**Vueコーディングルール:**
- `<script setup lang="ts">` を使用
- Composition API のみ使用（Options API 不可）
- Propsは `defineProps<T>()` で型定義
- Emitsは `defineEmits<T>()` で型定義
- テンプレート内はkebab-case (`my-component`)
- 1コンポーネント = 1ファイル（巨大化したら分割）

### 3.2 バックエンド (Python)

**ruff設定:**
```toml
# ruff.toml
target-version = "py311"
line-length = 100

[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM"]
ignore = ["E501"]

[format]
quote-style = "double"
indent-style = "space"
```

**mypy設定:**
```ini
# mypy.ini
[mypy]
python_version = 3.11
strict = true
warn_return_any = true
warn_unused_configs = true

[mypy-boto3.*]
ignore_missing_imports = true
```

**Pythonコーディングルール:**
- 型アノテーション必須（`mypy --strict` 通過）
- docstring は必要最小限（パブリック関数のみ）
- `from __future__ import annotations` を先頭に記述
- f-string を使用（`.format()` 不可）
- 例外は具体的な型を捕捉（`except Exception` 不可）
- 関数は1関数 = 1責務（最大50行目安）

### 3.3 インフラ（AWS CLI）

- Lambda デプロイ手順は `docs/lambda-deployment.md` を参照
- リソース命名は `counseling-demo-` プレフィックスを使用
- IAM ポリシーはインラインポリシーで管理

---

## 4. テスト規約

### 4.1 フロントエンド

| 種別 | ツール | 対象 | 目標カバレッジ |
|------|--------|------|---------------|
| E2Eテスト | Playwright | チャットフロー | 主要ユーザーストーリー |

**テストファイル配置:**
- E2Eテスト: `frontend/tests/counselor-search.spec.ts`
- ファイル名: `*.spec.ts`

**テスト実行:**
```bash
cd frontend
npm test                  # E2Eテスト実行
npm run test:headed       # ブラウザ表示付き
npm run test:debug        # デバッグモード
npm run test:report       # HTML レポート表示
```

### 4.2 バックエンド

| 種別 | ツール | 対象 | 目標カバレッジ |
|------|--------|------|---------------|
| ユニットテスト | pytest | validator, sql_builder, aggregator | 90%以上 |
| 統合テスト | pytest + moto | handler → Athena (moto) | 主要フロー |
| SQLテスト | pytest + 大文字比較 | 生成SQLの検証 | 全条件パターン |

**テストファイル配置:**
- `backend/tests/test_<module>.py`
- フィクスチャ: `conftest.py`
- テストデータ: `tests/events/`

**テスト実行:**
```bash
# フロントエンド
cd frontend && npm test

# バックエンド
cd backend && python -m pytest -v --mypy
```

### 4.3 テスト記述ルール

- テスト関数名: `test_<被検証対象>_<条件>_<期待結果>`
  - 例: `test_validate_conditions_invalid_station_returns_error`
- AAAパターン (Arrange / Act / Assert)
- フィクスチャで外部依存をモック
- テスト間で状態共有しない

---

## 5. Git規約

### 5.1 ブランチ戦略

```
main ← リリース済みコード
  └── feat/<feature-name> ← 機能開発
  └── fix/<bug-name> ← バグ修正
  └── docs/<topic> ← ドキュメント更新
  └── refactor/<scope> ← リファクタリング
```

### 5.2 コミットメッセージ

```
<type>(<scope>): <subject>

<body> (optional)

<footer> (optional)
```

| type | 用途 |
|------|------|
| feat | 新機能 |
| fix | バグ修正 |
| docs | ドキュメント更新 |
| style | コードスタイル変更（ロジック変更なし） |
| refactor | リファクタリング |
| test | テスト追加・修正 |
| chore | ビルド・ツール関連 |
| infra | インフラ変更 |

**例:**
```
feat(backend): add requested_datetime search logic

Implement absolute datetime and day-of-week search in sql_builder.py.
Adds tolerance_minutes support for fuzzy time matching.
```

### 5.3 プルリクエスト

- マージ前にCI通過必須
- レビュー1名以上承認
- コミットはスクエッシュ
- デスク립ションに影響範囲・テスト方法を記載

---

## 6. セットアップ手順

### 6.1 前提条件

```bash
# 必要ツール
aws --version        # AWS CLI v2
uv --version         # >= 0.7.6 (Pythonパッケージ管理)
node --version       # >= 24.9.0
python --version     # >= 3.11.15
```

### 6.2 フロントエンド

```bash
cd frontend
npm install
npm run dev          # 開発サーバー起動 (http://localhost:5173)
```

### 6.3 バックエンド

```bash
cd backend

# uv で仮想環境を初期化（Python 3.11.15使用）
uv init  # pyproject.toml を生成

# 依存関係をインストール（pyproject.toml と requirements.txt を同期）
uv sync

# 開発用依存関係も含める場合
uv sync --extra dev  # requirements-dev.txt に対応するextraを定義済みとみなす
```

`pyproject.toml` による依存関係管理:

```toml
[project]
name = "counselor-search-ai-backend"
version = "0.1.0"
requires-python = ">=3.11.15"

[project.dependencies]
boto3 >= 1.35.0,<2.0.0

[project.optional-dependencies]
dev = [
    "pytest >= 8.3.0,<9.0.0",
    "mypy >= 1.11.0,<2.0.0",
    "ruff >= 0.6.0,<1.0.0",
]
```

デプロイ時のエクスポート:

```bash
# requirements.txt をエクスポート（CI/CD等で使用）
uv export --format requirements.txt > requirements.txt
uv export --format requirements.txt --extra-dev > requirements-dev.txt
```

### 6.4 AWS設定

```bash
aws configure
# Access Key, Secret Key, Region (ap-northeast-1), Output (json)
```

### 6.5 データ投入

```bash
cd scripts
bash seed-data.sh
```

---

## 7. 開発コマンド

### フロントエンド

| コマンド | 用途 |
|---------|------|
| `npm run dev` | 開発サーバー起動 |
| `npm run build` | 本番ビルド |
| `npm run preview` | ビルド結果プレビュー |
| `npm test` | ユニットテスト実行 |
| `npm run lint` | ESLint実行 |
| `npm run lint:fix` | ESLint自動修正 |
| `npm run format` | Prettierフォーマット |
| `npm run type-check` | TypeScript型チェック |

### バックエンド

| コマンド | 用途 |
|---------|------|
| `python -m pytest -v` | テスト実行 |
| `python -m pytest -v --cov=src` | カバレッジ付きテスト |
| `python -m mypy src/` | 型チェック |
| `python -m ruff check src/` | リント |
| `python -m ruff format src/` | フォーマット |

### インフラ

| コマンド | 用途 |
|---------|------|
| `bash scripts/deploy.sh` | スタックデプロイ |
| `bash scripts/teardown.sh` | スタック削除 |
| `bash scripts/seed-data.sh` | データ投入 |

---

## 8. CI/CD

### 8.1 ワークフロー

```
GitHub Push
  ├── Frontend Lint + Type Check + Test
  ├── Backend Lint + Type Check + Test
  └── CloudFormation Validate (syntax only)
```

### 8.2 GitHub Actions (将来実装)

```yaml
# .github/workflows/ci.yml (概要)
name: CI
on: [push, pull_request]
jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm test

  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11.15' }
      - uses: actions/setup-node@v4
        with: { node-version: '24.9.0' }
      - run: uv sync  # requirements.txtから依存関係をインストール
      - run: uv run pytest -v --cov=src

  infra:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Lambda デプロイ手順は docs/lambda-deployment.md を参照"
```

---

## 9. デプロイ手順

### 9.1 Lambda デプロイ

Lambda デプロイ手順は [lambda-deployment.md](lambda-deployment.md) を参照してください。

```bash
# 1. バックエンドコードの zip 化
cd backend
zip -r /tmp/search_counselors.zip handler.py validator.py sql_builder.py aggregator.py models.py
cd ..

# 2. Lambda 関数更新
aws lambda update-function-code \
  --function-name search_counselors \
  --zip-file fileb:///tmp/search_counselors.zip \
  --region ap-northeast-1
```

### 9.2 プロキシ Lambda デプロイ

```bash
# 1. プロキシコードの zip 化
cd backend
zip -j /tmp/agentcore-proxy.zip proxy_handler.py
cd ..

# 2. Lambda 関数更新
aws lambda update-function-code \
  --function-name agentcore-proxy \
  --zip-file fileb:///tmp/agentcore-proxy.zip \
  --region ap-northeast-1
```

### 9.3 フロントエンドデプロイ (S3 Web Hosting)

```bash
cd frontend

# 1. ビルド
npm run build

# 2. S3 にアップロード
aws s3 sync dist s3://counselor-search-ai-frontend --delete
```

### 9.4 クリーンアップ

```bash
# Lambda 関数削除
aws lambda delete-function --function-name search_counselors --region ap-northeast-1
aws lambda delete-function --function-name agentcore-proxy --region ap-northeast-1

# IAM ポリシー削除
aws iam delete-role-policy --role-name lambda_role_himuro --policy-name CounselorSearchPolicy
aws iam delete-role-policy --role-name lambda_role_himuro --policy-name AgentCoreInvokePolicy

# API Gateway 削除
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='CounselorSearchAgentCoreProxy'].id" --output text)
aws apigateway delete-rest-api --rest-api-id $API_ID

# S3 ホスティングバケット削除
aws s3 rm s3://counselor-search-ai-frontend --recursive
aws s3 rb s3://counselor-search-ai-frontend

# S3 データバケット削除
aws s3 rm s3://counseling-demo-data --recursive
aws s3 rm s3://counseling-demo-athena-results --recursive
aws s3 rb s3://counseling-demo-data
aws s3 rb s3://counseling-demo-athena-results

# Glue テーブル・データベース削除
aws glue delete-table --database-name counseling_demo_db --name offices
aws glue delete-table --database-name counseling_demo_db --name counselors
aws glue delete-database --name counseling_demo_db

# Athena ワークグループ削除
aws athena delete-work-group --work-group counseling-demo-wg
```