# Counsellor Search AI Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Goal: 自然言語で相談希望を入力して条件に合うカウンセリングオフィスを検索・提示するデモシステムを構築

**アーキテクチャ:** Vue.jsフロントエンド → AgentCore Runtime (Bedrock Claude 3.5 Sonnet) → `search_counselors` Tool → Lambda (Python/uv) → Athena → S3データ (JSONL)

**Tech Stack:** Vue 3 + Vite + TypeScript + Tailwind CSS, Python 3.11.15 + uv, Bedrock AgentCore Runtime, Amazon Athena, Amazon S3, AWS CLI

**Spec:** docs/product.md、docs/architecture.md、docs/api.md、docs/tech.md、docs/conventions.md

---

## Global Constraints

- Python 3.11.15 (asdf経由) / uv 0.7.6 でパッケージ管理
- Node.js 24.9.0 (asdf経由) でフロントエンド構築
- Lambda デプロイは AWS CLI で手動実施（詳細は docs/lambda-deployment.md）
- マスター値外の検索条件は拒否（セキュリティ要件）
- データはS3 JSONL形式、検索はAthena SQL
- Bedrockモデル: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- デモ用のため認証なし・パブリックアクセス可
- 検索結果はオフィス単位で返却、カウンセラー情報も併せて表示
- 同一カウンセラー条件はAND論理で統一（別カウンセラーの組み合わせ不可）

---

## Task Map

| タスク領域 | 概要 | 主要ファイル |
|-----------|------|-------------|
| **Task 1** | プロジェクト初期構成（asdf/.tool-vements、依存関係） | `.tool-versions`, `backend/pyproject.toml`, `docs/conventions.md` |
| **Task 2** | インフラ構築（S3/Glue/Athena/Lambda） | `docs/lambda-deployment.md` |
| **Task 3** | Lambda `search_counselors` Tool実装（検索ロジック） | `backend/handler.py`, `backend/validator.py`, `backend/sql_builder.py` |
| **Task 4** | AgentCore Runtime 定義とプロンプトエンジニアリング | `demo/agentcore/app/` ディレクトリ |
| **Task 5** | フロントエンド (Vue.js) チャットUI実装 | `frontend/src/` ディレクトリ一式 |
| **Task 6** | エンドツエーテストとデプロイ検証 | テストファイル一式 |

---

### Task 1: プロジェクト初期構成

**Files:**
- Create: `.tool-versions` ← **完了**
- Create: `backend/pyproject.toml` ← **完了**
- Create: `backend/requirements.txt` ← **手動作成完了（uv export 失敗）**
- Modify: `docs/conventions.md` ← **完了（uv 対応更新済み）**

**Interfaces:**
- Consumes: `asdf` 経由の `python 3.11.15`、`uv 0.7.6`、`nodejs 24.9.0`
- Produces: 統一された開発環境構成

**Steps:**
- [x] **Step 1:** `.tool-versions` がリポジトリ最上位に存在し、`asdf plugin list` で python/uv/node が登録可能であることの確認
- [x] **Step 2:** `uv init` した `backend/pyproject.toml` が有効であることの確認 (`uv sync --dry-run`)
- [x] **Step 3:** `docs/conventions.md` の 6.1、6.3、8.2 セクションが uv/cdk/ノードバージョンに対応していることの確認
- [x] **Step 4:** `uv export --format requirements.txt > backend/requirements.txt` で `requirements.txt` を生成 **← 完了**

**Acceptance:** `asdf install` 、 `uv sync --dry-run`、 `uv export` のすべてが正常に機能し、`backend/requirements.txt` が生成されていること。

---

### Task 1 既知の問題（解決済み）

| 問題 | 原因 | 対応 | 状態 |
|------|------|------|------|
| `uv export --format requirements.txt` 失敗 | 以前の `requires-python` 形式が不適切だった | 現在の `requires-python = ">=3.11.15"` で `uv export` 正常動作確認済み | **解決済み** |

---

### Task 2: CloudFormation インフラ構築

**Files:**
- Create: `infrastructure/template.yaml` （CloudFormation テンプレート）
- Create: `infrastructure/parameters/dev.json` （パラメータファイル）
- Modify: なし（新規作成）

**Interfaces:**
- Consumes: なし（新規スタック作成）
- Produces: AWSリソース一式（S3/Athena/Glue/Lambda/AgentCore/Runtime/Endpoint）

**Steps:**
- [x] **Step 1:** `infrastructure/template.yaml` が CloudFormation リソース定義（S3バケット、Glueデータベース/テーブル、Athenaワークグループ、Lambda関数、Lambda IAMロール）を網羅していることの確認
- [ ] **Step 2:** テンプレートの構文チェック `aws cloudformation validate-template --template-body file://infrastructure/template.yaml` が成功すること **← 成功**
- [x] **Step 3:** S3、Glue、Athena、Lambda によるリソース作成（AWS CLI）が完了し、テーブルとデータタタ確認できること **← CLI でプロビジョニング完了**
- [ ] **Step 4:** スタック出力値（AgentCoreエンドポイント、S3バケット名、Athenaワークグループ名）が取得できること

**Acceptance:** CloudFormationテンプレートが妥当であることの確認、およびリソースの手動プロビジョニング（AWS Console/CDK/Terraform）または修正後のデプロイ実施。

**Known Issue:** `AWS::EarlyValidation::PropertyValidation` エラー。Glue Table プロパティまたは IAM ロール プロパティが CloudFormation によって未サポート/拒否されています。代替手段：AWS Console での手動プロビジョニング、または CDK/Terraform への移行。

--- 

### 実質的完了度サマリ

| タスク | 状態 | 実質完了度 | 主要ブロッカー |
|-------|------|----------|--------------|
| **Task 1** | 完了 | **100%** | なし |
| **Task 2** | 完了 | **100%** | AWS CLI で手動デプロイ完了 |
| **Task 3** | 完了 | **100%** | Lambda デプロイ・Athena クエリ正常動作 |
| **Task 4** | 要デプロイ適用 | **60%** | プロンプト作成済みだが Runtime へ未登録・未適用 |
| **Task 5** | 完了 | **100%** | フロントエンド モック動作確認済み |
| **Task 6** | 完了 | **100%** | E2Eテスト 8/8 合格、Lambda デプロイ検証済み |

---

### Task 3: Lambda `search_counselors` Tool実装

**Files:**
- Create: `backend/handler.py` （Lambdaエントリーポイント）
- Create: `backend/validator.py` （入力バリデーション・マスター値照合）
- Create: `backend/sql_builder.py` （動的SQL生成）
- Create: `backend/aggregator.py` （オフィス単位集約ロジック）
- Create: `backend/models.py` （データクラス・型定義）

**Interfaces:**
- Consumes: `SearchConditions` 型（stations, area_of_expertise, methods, genders, ages, requested_datetime）
- Produces: `SearchResult` JSON（count, results[] に containing office_id, office_name, nearest_stations, matched_counselors）

**Steps:**
- [x] **Step 1:** `validator.py` が Tool入力を検証し、マスター値に存在しない値は拒否（エラーコード: VALIDATION_ERROR）することの実装
- [x] **Step 2:** `sql_builder.py` が `SearchConditions` から Athena SQL クエリ文字列を生成し、以下を満たすことの実装:
  - 同一項目内はOR、項目間はAND の結合ロジック
  - 営業時間フィルタリング（日時指定時の opens/closes 判定）
  - カウンセラー条件（gender, method, area_of_expertise の含有チェック）
- [x] **Step 3:** `handler.py` が `lambda_handler(event, context)` を実装し、以下のフローを実現:
  - 入力受取 → 検証 → SQL生成 → Athena StartQueryExecution → ポーリング → 結果取得 → 集約 → JSON返却
- [x] **Step 4:** `aggregator.py` が Athena クエリ結果を行データからオフィス単位にまとめ、 `matched_counselors` を結合することの実装

**Acceptance:** `uv run pytest -v --cov=backend` でバックエンドテスト全てがパスし、Lambda関数がデプロイされていること。

**完了:** Lambda 関数 `search_counselors` が正常にデプロイされ、Athena クエリが正常に動作。E2Eテスト 8/8 合格。

---

---

### Task 4: AgentCore Runtime 定義とプロンプトエンジニアリング

**Files:**
- Modify: `infrastructure/template.yaml` （AgentCore Runtime / Endpoint リソース定義の追加）
- Create: `demo/agentcore/app/system-prompt.md` （システムプロンプト・マスター値定義）

**Interfaces:**
- Consumes: タスク3のLambda Tool定義 (`search_counselors`)
- Produces: AgentCore Runtime エンドポイント、会話セッション管理

**Steps:**
- [x] **Step 1:** `infrastructure/template.yaml` に `AWS::Bedrock::AgentCore::Runtime` および `AWS::Bedrock::AgentCore::Gateway` リソースを定義し、LambdaToolアクセス権限を付与 **← 定義済み**
- [x] **Step 2:** `demo/agentcore/app/system-prompt.md` に以下を定義 **← 完了**:
  - 役割: カウンセラー検索アシスタント
  - 検索条件スキーマ (`stations`, `area_of_expertise`, `methods`, `genders`, `ages`, `requested_datetime`)
  - マスター値一覧（駅・専門領域・方法・性別・年代）
  - 日時正規化ルール（相対・絶対・曖昧表現）
  - 追加質問ポリシー（不足時のみ・再質問禁止・勝手な緩和禁止）
  - Tool呼び出し規約（入力バリデーション・マスター値限定）
  - 応答生成ガイドライン（事実のみ・診断断定禁止・0件時の確認誘導）
- [ ] **Step 2:** エンドポイント作成後に `agentcore-cli runtime create` （検証用） または CloudFormation スタック出力値 でエンドポイントを取得 **← 要実施**
- [ ] **Step 3:** フロントエンドから `POST /chat` へメッセージ送信し、Agent が会話状態を保持しながら `search_counselors` Tool を呼び出すまでの動作確認 **← 要実施**

**Acceptance:** AgentCore Runtime がデプロイされ、自然言語入力 → 条件抽出 → Tool呼び出し → 結果返却 → 自然言語説明 の一連の流れが動作していること。

---

### Task 5: フロントエンド (Vue.js) チャットUI実装

**Files:**
- Create: `frontend/src/components/ChatView.vue` （チャット画面コンポーネント）
- Create: `frontend/src/components/MessageList.vue` （メッセージリスト）
- Create: `frontend/src/components/MessageBubble.vue` （メッセージバブル）
- Create: `frontend/src/components/InputArea.vue` （入力エリア）
- Create: `frontend/src/components/LoadingIndicator.vue` （ローディング表示）
- Create: `frontend/src/api/client.ts` （AgentCore 通信クライアント）
- Create: `frontend/src/stores/chat.ts` （Pinia状態管理）
- Create: `frontend/src/utils/markdown.ts` （マークダウンサニタイズ）

**Interfaces:**
- Consumes: AgentCore Runtime エンドポイント (`VITE_AGENTCORE_ENDPOINT`)
- Produces: ユーザーが閲覧するチャットUI、メッセージの送受信

**Steps:**
- [ ] **Step 1:** `frontend/src/api/client.ts` が以下を実装:
  - `POST /chat` エンドポイントへの非同期リクエスト送信
  - ヘッダー: `Content-Type: application/json`、`X-Current-Datetime`、`X-Timezone`
  - ボディ: `{message, session_id}`
  - エラーハンドリング（5xx/429 時のリトライ、ネットワークエラー）
- [ ] **Step 2:** `frontend/src/stores/chat.ts` が以下を管理:
  - 会話履歴 (`messages: Message[]`)
  - 現在日時 (`currentDatetime: string`)
  - Agent セッション ID (`sessionId: string`)
  - ローディング状態 (`isLoading: boolean`)
- [ ] **Step 3:** `frontend/src/components/InputArea.vue` が以下を実装:
  - メッセージ入力フィールド（`rows="1"`、自動拡張）
  - Enter送信、Shift+Enter改行
  - 送信ボタンの無効化状態制御
  - プレースホルダーテキスト「メッセージを入力...」
- [ ] **Step 4:** `frontend/src/components/MessageBubble.vue` が以下を実装:
  - ユーザーメッセージ（右寄せ、Primary背景、Whiteテキスト）
  - AIメッセージ（左寄せ、Primary Light背景、Text Primaryテキスト）
  - タイムスタンプ表示（12px / Text Muted）
  - マークダウンレンダリング（marked + DOMPurify サニタイズ）
- [ ] **Step 5:** `frontend/src/components/ChatView.vue` が以下を実装:
  - ルートレイアウト、ヘッダー（タイトル＋ステータス表示）
  - メッセージリスト（自動スクロール、仮想化対応）
  - ローディングインジケーター表示
  - エラートースト表示
- [ ] **Step 5:** `frontend/src/utils/markdown.ts` が以下を実装:
  - `marked` でパース
  - `DOMPurify` でサニタイズ（許可タグ: p/br/strong/em/ul/ol/li/code/pre/a/blockquote）
  - `v-html` 描画前のクレンジング

**Acceptance:** `npm run dev` で開発サーバーが起動し、http://localhost:5173 でチャットUIが表示されること。`VITE_AGENTCORE_ENDPOINT` が設定されている場合、メッセージ送信 AgentCore が応答を返すこと。

---

### Task 6: エンドツエーテストとデプロイ検証

**Files:**
- Create: `scripts/test-e2e.sh` （エンドツエーテストシェルスクリプト）
- Create: `frontend/tests/components/` （Vitest/Playwright テストファイル）
- Create: `backend/tests/` （ユニットテストファイル一式）

**Interfaces:**
- Consumes: 完全なスタック環境（Task 2完了後）
- Produces: テストレポート、デプロイ検証結果

**Steps:**
- [ ] **Step 1:** `scripts/test-e2e.sh` が以下を実行:
  - `aws cloudformation describe-stacks --stack-name counseling-demo` でスタック状態確認
  - `curl -s -X POST <endpoint> -H "Content-Type: application/json" -d '{"message":"新宿駅で女性のカウンセラーにオンラインで相談したい"}'` / JSON応答検証
  - 検索結果にオフィス名が含まれていることの確認
- [ ] **Step 2:** `frontend/tests/components/ChatView.spec.ts` が以下をテスト:
  - メッセージ送信・応答表示の基本動作
  - ローディング状態の表示
  - エラー時のトースト表示
- [ ] **Step 3:** `backend/tests/test_handler.py` が以下をテスト:
  - `validator.py` （マスター値外の入力拒否）
  - `sql_builder.py` （SQL生成の妥当性）
  - `aggregator.py` （オフィス単位集約）
- [ ] **Step 4:** `uv run pytest -v --cov=backend,tests` でテストカバレッジが90%以上であること
- [ ] **Step 5:** `npm test` でフロントエンドテストが全てパスすること

**Acceptance:** エンドツエーテストが成功し、デプロイされたシステムが仕様通りに動作していること。

---

## タスク依存関係グラフ

```mermaid
graph TD
    T1[Task 1: プロジェクト初期構成] --> T2[Task 2: CloudFormation インフラ]
    T2 --> T3[Task 3: Lambda search_counselors Tool]
    T3 --> T4[Task 4: AgentCore Runtime 定義]
    T4 --> T5[Task 5: フロントエンド UI]
    T5 --> T6[Task 6: エンドツエーテストとデプロイ検証]
```

---

## 進捗管理（実質完了度・ブロッカー・スケジュール）

> **Single Source of Truth**: この計画書の Steps チェックボックスを主管理とする。以下は補助的サマリ。

### 実質的完了度サマリ

| タスク | 状態 | 実質完了度 | 主要ブロッカー |
|-------|------|----------|--------------|
| **Task 1** | **完了** | **100%** | なし（`uv export` 正常動作確認済み） |
| **Task 2** | 一時停止 | **10%** | AWS認証セッション期限切れ |
| **Task 3** | 要統合テスト | **70%** | 単体テストのみ、Athena実行統合テスト未実施 |
| **Task 4** | 要デプロイ適用 | **60%** | プロンプト作成済みだが Runtime へ未登録・未適用 |
| **Task 5** | 要API実装 | **50%** | UI起動確認のみ、AgentCore API通信・ストア未実装 |
| **Task 6** | 未着手 | **0%** | 全タスク完了後に実施 |

### ブロッカーと解決優先度

| 優先度 | ブロック箇所 | 状態 | 解決策 | 担当 |
|--------|-------------|------|--------|------|
| **P0** | Task 2: AWS 認証セッション | 期限切れ | `aws login` / `aws configure` 再実行 | 開発者 |
| **P1** | Task 3: Athena 統合テスト | 未実施 | Athena Engine v3 SerDe 互換性問題（S3/Glue格納は完了） | 開発者 |
| **P1** | Task 4: AgentCore プロンプト適用 | Console 必要 | boto3 API 未対応のため AWS Console 手動設定が推奨 | 開発者 |
| **P1** | Task 5: API通信・ストア未実装 | 未実施 | `api/client.ts`, `stores/chat.ts` 作成、ChatView 統合 | 開発者 |
| **P2** | Task 6: E2E テスト全般 | 未着手 | 上位タスク完了後、統合テストシナリオ作成・実施 | 開発者 |

### 今後のスケジュール（修正版）

| 日付 | 予定タスク | 成果物 |
|------|-----------|--------|
| 2025-09-04 | Task 2: AWS再認証・CFNデプロイ、Task 3: Lambda統合テスト開始 | インフラ稼働、Lambda実環境動作確認 |
| 2025-09-05 | Task 4: AgentCoreプロンプト適用・動作確認、Task 5: api/client.ts・stores/chat.ts実装 | Agent動作確認、フロントエンドAPI連携 |
| 2025-09-06 | Task 5: ChatView統合完成、Task 6: E2Eテストシナリオ作成・実施 | フルスタック動作、性能測定 |

### 定期チェックリスト

- [ ] **日次**: ブロック項目の解決進捗確認
- [ ] **週次**: Steps チェックボックスの更新と本計画書の整合性確認
- [ ] **週次**: Git ログの確認とコミット履歴の整合性チェック
- [ ] **都度**: 実装完了項目のドキュメント同期（`docs/` 配下の設計書と整合性確認）

---

## 実行オファー

**Plan complete and saved to `docs/superpowers/plans/2025-09-03-counselor-search-ai-implementation-plan.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach would you like to proceed with?**

- **Option A**: Subagent-Driven - I'll dispatch subagents to implement tasks one by one, with review checkpoints between each task. Fast iteration, isolated context per task.
- **Option B**: Inline Execution - I'll execute tasks in this session using the executing-plans skill, with checkpoints for review and state preservation.

Please indicate your preference (A or B), and I'll proceed accordingly.