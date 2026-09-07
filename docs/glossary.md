# 用語定義（ユビキタス言語）：カウンセラー検索AIデモ

## 目次

1. [ドメイン用語](#1-ドメイン用語)
2. [技術用語](#2-技術用語)
3. [AWSサービス用語](#3-awsサービス用語)
4. [英日対応表](#4-英日対応表)
5. [コード上の命名規則](#5-コード上の命名規則)

---

## 1. ドメイン用語

| 用語 | 日本語 | 定義 | 使用箇所 |
|------|--------|------|---------|
| Counselor | カウンセラー | 心理カウンセリングを行う専門家 | データモデル |
| Office | カウンセリングオフィス | カウンセラーが所属する施設 | データモデル |
| Nearest Station | 最寄り駅 | オフィスの最寄り駅（複数可） | オフィスデータ |
| Opening Hours | 営業時間 | オフィスが営業する曜日・時間帯 | オフィスデータ |
| Area of Expertise | 専門領域 | カウンセラーが得意とする相談分野 | カウンセラーデータ |
| Method | カウンセリング方法 | 対面・オンライン・電話・チャット | カウンセラーデータ |
| Matched Counselor | 条件一致カウンセラー | 検索条件をすべて満たす同一カウンセラー | 検索結果 |
| Requested DateTime | 相談希望日時 | ユーザーが相談したい日時（絶対/相対/曖昧） | 検索条件 |

## 2. 技術用語

| 用語 | 定義 | 使用箇所 |
|------|------|---------|
| Tool | AI Agentから呼び出される検索関数 (`search_counselors`) | Agent → Lambda |
| Master Value | マスター値。検索条件として受け付ける固定値一覧 | Agent, Lambda |
| Tolerance Minutes | 曖昧な時間表現の許容誤差（分）。デフォルト60分 | 日時正規化 |
| Day of Week | 曜日名（英語）。Monday〜Sunday | 日時検索 |
| Absolute DateTime | 絶対日時。具体的な日付+時刻（ISO 8601） | 日時検索 |
| Relative Date | 相対日時。現在日時基準の「明日」「来週」等 | Agent日時解釈 |
| Fuzzy Time | 曖昧な時間表現。「14時ごろ」「午後」「夕方」等 | Agent日時解釈 |
| Aggregate | 集約。行データをオフィス単位にまとめる処理 | Lambda結果処理 |

## 3. AWSサービス用語

| サービス | 略称 | 定義 | 本システムでの役割 |
|---------|------|------|-------------------|
| Amazon Bedrock | Bedrock | マネージドLLMサービス | 自然言語理解・応答生成 |
| Bedrock AgentCore Runtime | AgentCore | AI Agent実行環境 | Agent管理・Tool連携 |
| AWS Lambda | Lambda | サーバーレスコンピューティング | search_counselors Tool実行 |
| Amazon Athena | Athena | サーバーレスSQL検索エンジン | S3上のJSONL検索 |
| AWS Glue Data Catalog | Glue | メタデータ管理 | Athenaテーブル定義 |
| Amazon S3 | S3 | オブジェクトストレージ | データ格納・検索結果保存 |
| CloudFormation | CFN | Infrastructure as Code | 全リソース管理 |
| Amazon CloudFront | CloudFront | CDN | フロントエンド配信 |

## 4. 英日対応表

| English | 日本語 | コード上の命名 |
|---------|--------|---------------|
| Office | オフィス | `office`, `OfficeResult` |
| Counselor | カウンセラー | `counselor`, `CounselorMatch` |
| Nearest Station | 最寄り駅 | `nearest_stations` |
| Opening Hours Specification | 営業時間指定 | `opening_hours_specification` |
| Area of Expertise | 専門領域 | `area_of_expertise` |
| Method | 相談方法 | `method` |
| Gender | 性別 | `gender` |
| Age | 年代 | `age` |
| Requested DateTime | 相談希望日時 | `requested_datetime` |
| Day of Week | 曜日 | `day_of_week` |
| Tolerance Minutes | 許容誤差（分） | `tolerance_minutes` |
| Search Conditions | 検索条件 | `SearchConditions` |
| Search Result | 検索結果 | `SearchResult` |
| Matched Counselors | 条件一致カウンセラー | `matched_counselors` |

## 5. コード上の命名規則

### 5.1 変数・関数名（Python）

| 対象 | ルール | 例 |
|------|--------|-----|
| 検索条件変数 | snake_case | `stations`, `requested_datetime` |
| SQL構築関数 | snake_case | `build_search_sql()` |
| バリデーション関数 | snake_case | `validate_conditions()` |
| Athena実行関数 | snake_case | `start_query()`, `wait_for_completion()` |
| 結果集約関数 | snake_case | `aggregate_offices()` |
| エスケープ関数 | snake_case | `escape_sql()` |

### 5.2 変数・型名（TypeScript）

| 対象 | ルール | 例 |
|------|--------|-----|
| インターフェース | PascalCase | `SearchConditions`, `OfficeResult` |
| 状態変数 | camelCase | `isLoading`, `messageList` |
| 関数 | camelCase | `validateConditions()`, `sendMessage()` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |

### 5.3 ファイル名

| 対象 | ルール | 例 |
|------|--------|-----|
| Pythonモジュール | snake_case | `sql_builder.py`, `validator.py` |
| TypeScriptモジュール | camelCase | `useChat.ts`, `client.ts` |
| Vueコンポーネント | PascalCase | `ChatView.vue`, `MessageBubble.vue` |
| データファイル | snake_case | `offices.jsonl`, `master_stations.json` |