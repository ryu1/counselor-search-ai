# 運用手順書：カウンセラー検索AIデモ

## 目次

1. [動作モード](#1-動作モード)
2. [日常運用](#2-日常運用)
3. [ログ確認](#3-ログ確認)
4. [障害対応](#4-障害対応)
5. [鍵・認証情報管理](#5-鍵認証情報管理)
6. [デプロイ前チェックリスト](#6-デプロイ前チェックリスト)
7. [クリーンアップ](#7-クリーンアップ)

---

## 1. 動作モード

### 1.1 デモ環境

| 項目 | 設定 |
|------|------|
| 環境名 | `demo` |
| AWSアカウント | 使用中のアカウント |
| リージョン | `ap-northeast-1` (東京) |
| スタック名 | `counseling-demo` |
| 公開範囲 | パブリック（認証なし） |
| データ | 14オフィス・サンプルカウンセラー |

### 1.2 環境変数

| 変数名 | 必須 | 説明 | 例 |
|-------|------|------|-----|
| `AWS_REGION` | Yes | AWSリージョン | `ap-northeast-1` |
| `DATA_BUCKET` | Yes | データS3バケット名 | `counselor-search-ai-data-<account-id>` |
| `ATHENA_RESULT_BUCKET` | Yes | Athena結果バケット名 | `counselor-search-ai-athena-results-<account-id>` |
| `ATHENA_WORKGROUP` | Yes | Athena WorkGroup名 | `counseling-demo-wg` |
| `GLUE_DATABASE` | Yes | Glue Database名 | `counseling_demo` |
| `VITE_AGENTCORE_ENDPOINT` | Yes | AgentCore Runtime エンドポイント | CloudFormation出力値 |

---

## 2. 日常運用

### 2.1 デモ実施手順

```bash
# 1. デプロイ確認
aws cloudformation describe-stacks \
  --stack-name counseling-demo \
  --query 'Stacks[0].StackStatus' \
  --output text

# 2. フロントエンド起動確認
curl -s https://<cloudfront-domain>/ | head -5

# 3. AgentCoreエンドポイント確認
aws cloudformation describe-stacks \
  --stack-name counseling-demo \
  --query 'Stacks[0].Outputs' \
  --output table
```

### 2.2 データ更新手順

```bash
# オフィスデータ更新
aws s3 cp new_offices.jsonl s3://counselor-search-ai-data-<account-id>/offices/offices.jsonl

# カウンセラーデータ更新
aws s3 cp new_counselors.jsonl s3://counselor-search-ai-data-<account-id>/counselors/counselors.jsonl

# ※ Athenaはスケーマレス（JSONL追加で自動反映）
# ※ 大規模データ変更時はGlue partition更新が必要
```

### 2.3 コスト確認

```bash
# 月次コスト概算
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '1 month ago' +%Y-%m-01),End=$(date +%Y-%m-01) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[?contains(Metrics.UnblendedCost.Amount, `0`) == `false`]' \
  --output table
```

---

## 3. ログ確認

### 3.1 Lambdaログ

```bash
# 最新ログ取得
aws logs get-log-events \
  --log-group-name "/aws/lambda/counseling-demo-search-counselors" \
  --log-stream-name $(aws logs describe-log-streams \
    --log-group-name "/aws/lambda/counseling-demo-search-counselors" \
    --order-by LastEventTime \
    --descending \
    --limit 1 \
    --query 'logStreams[0].logStreamName' \
    --output text) \
  --limit 50 \
  --query 'events[].message' \
  --output text
```

### 3.2 AgentCoreログ

```bash
# AgentCore Runtime ログ
aws logs get-log-events \
  --log-group-name "/aws/bedrock-agentcore/counseling-demo-agent" \
  --log-stream-name <stream-name> \
  --limit 50 \
  --query 'events[].message' \
  --output text
```

### 3.3 Athenaクエリ実行履歴

```bash
# 最新クエリ実行状態
aws athena list-query-executions \
  --work-group counseling-demo-wg \
  --max-results 5 \
  --query 'QueryExecutionIds[]' \
  --output text
```

---

## 4. 障害対応

### 4.1 症状別切り分け

#### チャット応答がない

| 確認手順 | 操作 | 期待値 |
|---------|------|--------|
| 1. フロントエンドからAgentCore疎通 | curl + endpoint | 200 |
| 2. AgentCoreログ確認 | CloudWatch Logs | エラーなし |
| 3. Bedrockモデルアクセス確認 | AWSコンソール | 有効 |
| 4. IAMロール確認 | IAMコンソール | 権限あり |

#### 検索結果が0件

| 確認手順 | 操作 | 期待値 |
|---------|------|--------|
| 1. Lambdaログ確認 | CloudWatch Logs | SQL生成ログあり |
| 2. Athenaクエリ確認 | Athenaコンソール | 実行成功 |
| 3. S3データ確認 | S3コンソール | JSONLファイル存在 |
| 4. Glueテーブル確認 | Glueコンソール | スキーマ一致 |

#### Lambdaタイムアウト

| 確認手順 | 操作 | 期待値 |
|---------|------|--------|
| 1. Lambda実行時間確認 | CloudWatch Logs | < 300秒 |
| 2. Athenaクエリ実行時間 | Athenaクエリ統計 | < 60秒 |
| 3. S3データ量確認 | S3コンソール | データ量妥当 |
| 4. Lambdaメモリ増加検討 | CloudFormation | 256MB → 512MB |

#### SQL構文エラー

| 確認手順 | 操作 | 期待値 |
|---------|------|--------|
| 1. Lambda出力SQL確認 | CloudWatch Logs | SQLログ |
| 2. Athenaコンソールで手動実行 | Athena | エラー詳細取得 |
| 3. Glueスキーマ確認 | Glueコンソール | カラム名一致 |
| 4. Athena Engineバージョン確認 | Athena | Engine v3 |

### 4.2 緊急時対応

| 状況 | 対応 |
|------|------|
| Lambda異常高コスト | Lambda同時実行数制限を一時的に引き下げ |
| S3データアクセス異常 | S3バケットポリシーでアクセス制限 |
| AgentCore障害 | フロントエンドにエラーメッセージ表示（自動復旧待ち） |
| 全体障害 | CloudFormationスタック削除 → 再デプロイ |

---

## 5. 鍵・認証情報管理

### 5.1 環境変数

| 認証情報 | 場所 | 管理方法 |
|---------|------|---------|
| AWS Access Key | `~/.aws/credentials` | ローカル環境 |
| AgentCoreエンドポイント | `frontend/.env.local` | Git除外 |
| BedrockモデルID | CloudFormationテンプレート | コード管理（公開可） |

### 5.2 .gitignore

```gitignore
# 認証情報
.env
.env.local
.env.*.local
credentials
*.pem
*.key

# AWS
.aws/
```

### 5.3 定期確認

- [ ] 月1回: .gitignoreに認証情報ファイルが含まれるか確認
- [ ] 月1回: IAMロールの権限が最小か確認
- [ ] 月1回: 不要な環境変数がないか確認

---

## 6. デプロイ前チェックリスト

### 6.1 インフラ

- [ ] CloudFormationテンプレートの構文エラーがない
- [ ] S3バケット名がグローバルユニーク
- [ ] IAMロールが最小権限
- [ ] Lambdaメモリ・タイムアウト設定が妥当
- [ ] Athena WorkGroupの結果保存先が設定済み

### 6.2 データ

- [ ] `offices.jsonl` のスキーマが一致
- [ ] `counselors.jsonl` のスキーマが一致
- [ ] マスターデータファイルが5ファイル揃っている
- [ ] 個人情報がデモデータに含まれていない
- [ ] エンコーディングがUTF-8

### 6.3 フロントエンド

- [ ] `VITE_AGENTCORE_ENDPOINT` が設定済み
- [ ] `npm run build` が成功
- [ ] `npm run lint` が通過
- [ ] `npm run type-check` が通過
- [ ] `npm test` が通過

### 6.4 セキュリティ

- [ ] S3 Block Public Access が有効
- [ ] Lambda環境変数にAPIキーが含まれない
- [ ] CSPメタタグが設定済み
- [ ] DOMPurifyが有効

---

## 7. クリーンアップ

### 7.1 手動クリーンアップ

```bash
# 1. S3バケット内容削除
aws s3 rm s3://counselor-search-ai-data-<account-id> --recursive
aws s3 rm s3://counselor-search-ai-athena-results-<account-id> --recursive
aws s3 rm s3://counselor-search-ai-frontend-<account-id> --recursive

# 2. CloudFormationスタック削除
bash scripts/teardown.sh
```

### 7.2 自動クリーンアップ（将来）

```yaml
# CloudFormation スタック作成時にオプション
Resources:
  DataBucket:
    Type: AWS::S3::Bucket
    DeletionPolicy: Delete  # スタック削除時にバケットも削除
```

### 7.3 削除確認

```bash
# スタック削除完了確認
aws cloudformation describe-stacks \
  --stack-name counseling-demo \
  --query 'Stacks[0].StackStatus' \
  --output text
# 期待: DELETE_COMPLETE

# 残存リソース確認
aws s3 ls | grep counseling-demo
# 期待: 出力なし
```