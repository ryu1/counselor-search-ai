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

### 7.1 削除対象リソース一覧

| カテゴリ | リソース名 | 削除方法 |
|---------|----------|---------|
| S3 | `counseling-demo-data` | `aws s3 rb --force` |
| S3 | `counseling-demo-athena-results` | `aws s3 rb --force` |
| S3 | `counselor-search-ai-frontend` | `aws s3 rb --force` |
| Lambda | `search_counselors` | `aws lambda delete-function` |
| Lambda | `agentcore-proxy` | `aws lambda delete-function` |
| API Gateway | `CounselorSearchAgentCoreProxy` | `aws apigateway delete-rest-api` |
| Glue | データベース `counseling_demo_db` | `aws glue delete-database` |
| Glue | テーブル `offices`, `counselors` | `aws glue delete-table` |
| Athena | ワークグループ `counseling-demo-wg` | `aws athena delete-work-group --recursive-delete-option` |
| IAM | インラインポリシー `CounselorSearchPolicy` | `aws iam delete-role-policy` |
| IAM | インラインポリシー `AgentCoreInvokePolicy` | `aws iam delete-role-policy` |
| CloudWatch | ロググループ（4つ） | `aws logs delete-log-group` |
| CloudFormation | スタック `AgentCore-CounselorSearchAI-default` | `aws cloudformation delete-stack` |

**注意**: `lambda_role_himuro` は共有ロールのため削除しない。インラインポリシーのみ削除する。

### 7.2 手動クリーンアップ手順

```bash
# ===== 1. S3バケット内容削除 =====
aws s3 rm s3://counseling-demo-data --recursive
aws s3 rm s3://counseling-demo-athena-results --recursive
aws s3 rm s3://counselor-search-ai-frontend --recursive

# ===== 2. Lambda関数削除 =====
aws lambda delete-function --function-name search_counselors --region ap-northeast-1
aws lambda delete-function --function-name agentcore-proxy --region ap-northeast-1

# ===== 3. API Gateway削除 =====
API_ID=$(aws apigateway get-rest-apis \
  --query "items[?name=='CounselorSearchAgentCoreProxy'].id" \
  --output text --region ap-northeast-1)
aws apigateway delete-rest-api --rest-api-id $API_ID --region ap-northeast-1

# ===== 4. Glueテーブル・データベース削除 =====
aws glue delete-table --database-name counseling_demo_db --name offices --region ap-northeast-1
aws glue delete-table --database-name counseling_demo_db --name counselors --region ap-northeast-1
aws glue delete-database --name counseling_demo_db --region ap-northeast-1

# ===== 5. Athenaワークグループ削除 =====
aws athena delete-work-group \
  --work-group counseling-demo-wg \
  --recursive-delete-option \
  --region ap-northeast-1

# ===== 6. S3バケット削除 =====
aws s3 rb s3://counseling-demo-data --region ap-northeast-1
aws s3 rb s3://counseling-demo-athena-results --region ap-northeast-1
aws s3 rb s3://counselor-search-ai-frontend --region ap-northeast-1

# ===== 7. IAMインラインポリシー削除 =====
aws iam delete-role-policy \
  --role-name lambda_role_himuro \
  --policy-name CounselorSearchPolicy
aws iam delete-role-policy \
  --role-name lambda_role_himuro \
  --policy-name AgentCoreInvokePolicy

# ===== 8. CloudWatch Logs削除 =====
aws logs delete-log-group \
  --log-group-name "/aws/lambda/search_counselors" --region ap-northeast-1
aws logs delete-log-group \
  --log-group-name "/aws/lambda/agentcore-proxy" --region ap-northeast-1
aws logs delete-log-group \
  --log-group-name "/aws/bedrock-agentcore/runtimes/CounselorSearchAI_counselor_search_agent-1UyHcYHZG3-DEFAULT" \
  --region ap-northeast-1
aws logs delete-log-group \
  --log-group-name "/aws/bedrock-agentcore/runtimes/CounselorSearchAI_counselor_search_agent-KlIOGyAYbm-DEFAULT" \
  --region ap-northeast-1

# ===== 9. AgentCore CloudFormationスタック削除 =====
aws cloudformation delete-stack \
  --stack-name AgentCore-CounselorSearchAI-default \
  --region ap-northeast-1
aws cloudformation wait stack-delete-complete \
  --stack-name AgentCore-CounselorSearchAI-default \
  --region ap-northeast-1
```

### 7.3 削除確認

```bash
# S3バケット確認
aws s3 ls | grep -E "counseling|counselor-search"
# 期待: 出力なし

# Lambda関数確認
aws lambda list-functions \
  --query "Functions[?contains(FunctionName, \`search_counselors\`) || contains(FunctionName, \`agentcore-proxy\`)].FunctionName" \
  --output text --region ap-northeast-1
# 期待: 出力なし

# API Gateway確認
aws apigateway get-rest-apis \
  --query "items[?contains(name, \`CounselorSearch\`)].name" \
  --output text --region ap-northeast-1
# 期待: 出力なし

# Glue確認
aws glue get-databases \
  --query "DatabaseList[?contains(Name, \`counseling\`)].Name" \
  --output text --region ap-northeast-1
# 期待: 出力なし

# Athenaワークグループ確認
aws athena list-work-groups \
  --query "WorkGroups[?contains(Name, \`counseling\`)].Name" \
  --output text --region ap-northeast-1
# 期待: 出力なし

# CloudWatch Logs確認
aws logs describe-log-groups \
  --query "logGroups[?contains(logGroupName, \`counseling\`) || contains(logGroupName, \`search_counselors\`) || contains(logGroupName, \`agentcore\`)].logGroupName" \
  --output text --region ap-northeast-1
# 期待: 出力なし

# IAMポリシー確認
aws iam list-role-policies --role-name lambda_role_himuro \
  --query "PolicyNames[?contains(@, \`Counselor\`) || contains(@, \`AgentCore\`)]" \
  --output text
# 期待: 出力なし

# CloudFormationスタック確認
aws cloudformation describe-stacks \
  --stack-name AgentCore-CounselorSearchAI-default \
  --region ap-northeast-1 2>&1
# 期待: Stack with id AgentCore-CounselorSearchAI-default does not exist
```

### 7.4 注意事項

- **Athena ワークグループ**: `--recursive-delete-option` を指定しないと、クエリ実行履歴があるため削除エラーになる。必ずこのフラグを付けること。
- **S3 バケット**: バケット内のオブジェクトを先に削除してからバケットを削除する。`--force` フラグでも一括削除可能だが、念のため先に中身を空にする。
- **AgentCore CloudFormation スタック**: CDK でデプロイされたスタック。`wait stack-delete-complete` で削除完了を待つ。
- **共有 IAM ロール**: `lambda_role_himuro` は他のプロジェクトで使用中の可能性があるため、ロール自体は削除しない。インラインポリシーのみ削除する。
- **CloudWatch Logs**: Lambda 関数削除後もロググループが残るため、明示的に削除する必要がある。