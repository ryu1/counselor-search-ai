# 技術選定書：カウンセラー検索AIデモ

## 1. テクノロジースタック

### 1.1 フロントエンド

| 項目 | 選定 | 理由 |
|------|------|------|
| フレームワーク | Vue 3 (Composition API) | 軽量・習得コスト低・リアクティビティ |
| ビルド | Vite | 高速ホットリロード・ESMベース |
| 状態管理 | Pinia | Vue公式推奨・TypeScript対応 |
| スタイリング | Tailwind CSS | ユーティリティファースト・素早くCSS構築 |
| HTTPクライアント | fetch API (ネイティブ) | 外部依存なし・Fetch API標準 |
| マークダウン | marked + DOMPurify | AI応答レンダリング・XSS対策 |
| アイコン | unplugin-icons + Lucide | フレームワーク非依存・オンデマンド読み込み |
| TypeScript | — | 型安全性・開発体験向上 |

### 1.2 バックエンド（AWS）

| サービス | 用途 | 理由 |
|---------|------|------|
| Amazon Bedrock | LLM (Claude 3.5 Sonnet) | 日本語対応・Tool利用対応・マネージド |
| Bedrock AgentCore Runtime | AI Agent実行環境 | マネージドAgent基盤・Tool連携簡易 |
| AWS Lambda | 検索Tool実行 | サーバーレス・コスト効率・自動スケール |
| Amazon Athena | SQL検索エンジン | サーバーレス・S3直結・低コスト |
| AWS Glue Data Catalog | Athenaテーブル定義 | JSONL対応・スキーマ管理 |
| Amazon S3 | データ格納・検索結果 | 安定性・低コスト・Athena連携 |
| CloudFormation | Infrastructure as Code | AWS公式IaC・スタック管理 |

### 1.3 開発ツール

| ツール | 用途 | 理由 |
|-------|------|------|
| Python 3.11 | Lambdaランタイム | 高速・型注釈対応・Athena boto3対応 |
| boto3 | AWS SDK | Lambda内Athena操作 |
| pytest | テストフレームワーク | Python標準的・フィクスチャ充実 |
| mypy | 型チェッカー | 静的型検証 |
| ruff | リンター・フォーマッター | 高速・複数ルール統合 |
| Node.js 20 LTS | フロントエンドビルド | Vite要求バージョン |
| ESLint | TypeScriptリンター | Vue公式推奨 |
| Prettier | コードフォーマッター | 統一フォーマット |

---

## 2. 技術的制約と要件

| 要件 | 設定 |
|------|------|
| AWSリージョン | `ap-northeast-1` (東京) |
| Lambdaランタイム | Python 3.11 |
| Lambda最大実行時間 | 300秒 (5分) |
| Lambdaメモリ | 256MB (Athena API呼び出しのみ) |
| Lambda最大エージェントメモリ | 128MB |
| Lambda一時的ストレージ | 512MB |
| S3バケット | ACL無効・Block Public Access有効 |
| Athena WorkGroup | `counseling-demo-wg` |
| Athenaクエリ結果 | 最大1000行・超える場合はページネーション |
| Bedrockモデル | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| Bedrock最大入力トークン | 200,000 |
| Bedrock最大出力トークン | 8,192 |
| Vue.js | 3.4.x+ |
| Node.js | 20 LTS |
| TypeScript | 5.x |

---

## 3. パフォーマンス要件

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| チャット応答時間（検索なし） | < 3秒 | Agent応答（LLM推論のみ） |
| チャット応答時間（検索あり） | < 10秒 | Agent + Lambda + Athena |
| Lambda冷間起動 | < 3秒 | CloudWatch Logs |
| Athenaクエリ実行時間 | < 2秒 | Athenaクエリ統計 |
| フロントエンド初回読み込み | < 2秒 | Lighthouse |
| フロントエンドバンドルサイズ | < 200KB (gzipped) | Viteビルド出力 |

---

## 4. 選定根拠・代替案

| 選定 | 代替案 |却下理由 |
|------|--------|--------|
| Vue 3 | React | プロジェクト規模でVue軽量・習得コスト優先 |
| S3 + Athena | RDS | 常時稼働不要・デモ規模でDBサーバー過大 |
| S3 + Athena | OpenSearch | データ量小・コスト/運用複雑さ高 |
| Lambda | ECS Fargate | デモ規模でサーバーレス適切・常時稼働不要 |
| CloudFormation | CDK / Terraform | AWS公式・YAML記述で可視性高い・デモ向け |
| Bedrock Claude | OpenAI API | AWS統合・Tool機能・日本語品質 |
| AgentCore Runtime | 自前Agentサーバー | マネージド・運用負荷最小 |
| Tailwind CSS | CSS Modules | 高速開発・ユーティリティで一貫したデザイン |
| marked + DOMPurify | 整形済みHTML返却 | セキュリティ・拡張性 |

---

## 5. ライブラリバージョン

### フロントエンド (`frontend/package.json`)

```json
{
  "name": "counselor-search-ai",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "engines": {
    "node": ">=20.0.0"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "pinia": "^2.2.0",
    "marked": "^14.0.0",
    "dompurify": "^3.1.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vue-tsc": "^2.1.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "unplugin-icons": "^0.20.0",
    "lucide-static": "^0.400.0",
    "eslint": "^9.9.0",
    "@vue/eslint-config-typescript": "^14.0.0",
    "prettier": "^3.3.0",
    "msw": "^2.3.0"
  }
}
```

### バックエンド (`backend/requirements.txt` / `backend/pyproject.toml`)

Pythonパッケージは `pyproject.toml` で管理し、依存関係は以下の通り。

**pyproject.toml**（プロジェクトルート `backend/` に配置）:

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

**requirements.txt**（`uv export` で自動生成・デプロイ時使用）:

```bash
# requirements.txt を生成（デプロイ用）
uv export --format requirements.txt > requirements.txt

# 開発用も含める場合
uv export --format requirements.txt --extra-dev > requirements-dev.txt
```

ライブラリ一覧:

- **本体**: `boto3>=1.35.0,<2.0.0`
- **開発**: `pytest>=8.3.0,<9.0.0`, `mypy>=1.11.0,<2.0.0`, `ruff>=0.6.0,<1.0.0`
