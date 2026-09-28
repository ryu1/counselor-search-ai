# Lambda デプロイ手順

このドキュメントは Lambda 関数の手動デプロイ手順を記録したものです。

## 前提条件

- AWS CLI v2 が設定済み
- アカウント: `334107163417`
- リージョン: `ap-northeast-1`

## リソース構成図

```
User Request
    ↓
S3 Web Hosting (フロントエンド)
    ↓
API Gateway (IP制限あり)
    ↓
agentcore-proxy (Lambda)
    ↓
AgentCore Runtime (Bedrock)
    ↓
search_counselors (Lambda)
    ↓
Athena → S3 (counseling-demo-data)
```

## 1. S3 バケット作成

```bash
aws s3 mb s3://counseling-demo-data --region ap-northeast-1
aws s3 mb s3://counseling-demo-athena-results --region ap-northeast-1
```

## 2. S3 データ投入

```bash
# オフィスデータ
aws s3 cp backend/data/offices/office1.json s3://counseling-demo-data/offices/
aws s3 cp backend/data/offices/office2.json s3://counseling-demo-data/offices/

# カウンセラーデータ
aws s3 cp backend/data/counselors/counselor1.json s3://counseling-demo-data/counselors/
aws s3 cp backend/data/counselors/counselor2.json s3://counseling-demo-data/counselors/
```

## 3. Glue データベース・テーブル作成

```bash
aws glue create-database --database-input '{"Name": "counseling_demo_db"}'
```

### offices テーブル

```bash
aws glue create-table --database-name counseling_demo_db --table-input '{
  "Name": "offices",
  "StorageDescriptor": {
    "Columns": [
      {"Name": "id", "Type": "string"},
      {"Name": "office_name", "Type": "string"},
      {"Name": "nearest_stations", "Type": "array<string>"},
      {"Name": "opening_hours_specification", "Type": "array<struct<dayOfWeek:string,opens:string,closes:string>>"}
    ],
    "Location": "s3://counseling-demo-data/offices/",
    "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
    "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
    "SerdeInfo": {
      "SerializationLibrary": "org.openx.data.jsonserde.JsonSerDe",
      "Parameters": {"serialization.format": "1"}
    }
  },
  "TableType": "EXTERNAL_TABLE",
  "Parameters": {"serialization_format": "1"}
}'
```

### counselors テーブル

```bash
aws glue create-table --database-name counseling_demo_db --table-input '{
  "Name": "counselors",
  "StorageDescriptor": {
    "Columns": [
      {"Name": "office_id", "Type": "string"},
      {"Name": "name", "Type": "string"},
      {"Name": "area_of_expertise", "Type": "array<string>"},
      {"Name": "gender", "Type": "string"},
      {"Name": "method", "Type": "array<string>"},
      {"Name": "age", "Type": "string"}
    ],
    "Location": "s3://counseling-demo-data/counselors/",
    "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
    "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
    "SerdeInfo": {
      "SerializationLibrary": "org.openx.data.jsonserde.JsonSerDe",
      "Parameters": {"serialization.format": "1"}
    }
  },
  "TableType": "EXTERNAL_TABLE",
  "Parameters": {"serialization_format": "1"}
}'
```

## 4. Athena ワークグループ作成

```bash
aws athena create-work-group --name counseling-demo-wg --configuration '{
  "ResultConfiguration": {
    "OutputLocation": "s3://counseling-demo-athena-results/query-results/"
  },
  "EnforceWorkGroupConfiguration": true
}'
```

## 5. IAM ロール・ポリシー設定

既存の `lambda_role_himuro` ロールにカスタムポリシーを追加:

```bash
aws iam put-role-policy \
  --role-name lambda_role_himuro \
  --policy-name CounselorSearchPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:ListBucket"],
        "Resource": [
          "arn:aws:s3:::counseling-demo-data",
          "arn:aws:s3:::counseling-demo-data/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject", "s3:PutObject", "s3:ListBucket",
          "s3:DeleteObject", "s3:GetBucketAcl", "s3:GetBucketLocation"
        ],
        "Resource": [
          "arn:aws:s3:::counseling-demo-athena-results",
          "arn:aws:s3:::counseling-demo-athena-results/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "athena:StartQueryExecution", "athena:GetQueryExecution",
          "athena:GetQueryResults", "athena:StopQueryExecution",
          "athena:GetWorkGroup"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": ["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions"],
        "Resource": "*"
      }
    ]
  }'
```

## 6. S3 バケットポリシー

Athena と Lambda ロールの両方からの書き込みを許可:

```bash
aws s3api put-bucket-policy \
  --bucket counseling-demo-athena-results \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowAthenaQueryResults",
        "Effect": "Allow",
        "Principal": {"Service": "athena.amazonaws.com"},
        "Action": [
          "s3:GetObject", "s3:PutObject",
          "s3:ListBucket", "s3:DeleteObject"
        ],
        "Resource": [
          "arn:aws:s3:::counseling-demo-athena-results",
          "arn:aws:s3:::counseling-demo-athena-results/*"
        ]
      },
      {
        "Sid": "AllowLambdaRole",
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::334107163417:role/lambda_role_himuro"
        },
        "Action": [
          "s3:GetObject", "s3:PutObject",
          "s3:ListBucket", "s3:DeleteObject"
        ],
        "Resource": [
          "arn:aws:s3:::counseling-demo-athena-results",
          "arn:aws:s3:::counseling-demo-athena-results/*"
        ]
      }
    ]
  }'
```

## 7. Lambda 関数デプロイ

### zip パッケージ作成

```bash
cd backend
zip -r /tmp/search_counselors.zip \
  handler.py validator.py sql_builder.py aggregator.py models.py
cd ..
```

### Lambda 関数作成

```bash
aws lambda create-function \
  --function-name search_counselors \
  --runtime python3.11 \
  --handler handler.lambda_handler \
  --role arn:aws:iam::334107163417:role/lambda_role_himuro \
  --zip-file fileb:///tmp/search_counselors.zip \
  --timeout 300 \
  --memory-size 128 \
  --region ap-northeast-1
```

### 環境変数設定

```bash
aws lambda update-function-configuration \
  --function-name search_counselors \
  --environment '{
    "Variables": {
      "DATA_BUCKET": "counseling-demo-data",
      "ATHENA_RESULTS_BUCKET": "counseling-demo-athena-results",
      "ATHENA_WORKGROUP": "counseling-demo-wg"
    }
  }' \
  --region ap-northeast-1
```

### コード更新時

```bash
cd backend
zip -r /tmp/search_counselors.zip \
  handler.py validator.py sql_builder.py aggregator.py models.py
cd ..

aws lambda update-function-code \
  --function-name search_counselors \
  --zip-file fileb:///tmp/search_counselors.zip \
  --region ap-northeast-1
```

## 8. 動作確認

```bash
aws lambda invoke \
  --function-name search_counselors \
  --payload '{
    "parameters": {
      "stations": ["新宿駅"],
      "area_of_expertise": ["うつ"],
      "methods": ["オンライン"],
      "genders": ["男性"],
      "ages": ["30代"],
      "requested_datetime": "2026-09-12T10:00"
    }
  }' \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json

cat /tmp/response.json | python3 -m json.tool
```

## 注意事項

### なぜ CloudFormation/CDK を使わないのか

1. CloudFormation テンプレートの直接デプロイは `EarlyValidation::PropertyValidation` エラーで失敗
2. AgentCore CDK プロジェクトの `agentcore.json` spec が空でリソース作成不可
3. 詳細な原因解明よりも、デモ環境の早期構築を優先

### IAM ポリシーの伝播

- インラインポリシー変更後、数秒〜数十秒の伝播遅延が発生
- テスト失敗時は一度待ってからリトライすること

### Glue テーブルスキーマ

- S3 の JSON キー名と Glue カラム名を一致させること
- `SerdeInfo.SerializationLibrary` は `org.openx.data.jsonserde.JsonSerDe` を指定

### Athena バケット検証

- `BucketOwnerEnforced` 設定のバケットでは、バケットポリシーに Lambda ロールを明示的に追加する必要あり
- `ResultConfiguration` をワークグループに設定し、`EnforceWorkGroupConfiguration: true` にする

---

## agentcore-proxy Lambda デプロイ

### 概要

フロントエンドから AgentCore Runtime を呼び出すためのプロキシ Lambda 関数です。

### zip パッケージ作成

```bash
cd backend
zip -j /tmp/agentcore-proxy.zip proxy_handler.py
cd ..
```

### Lambda 関数作成

```bash
aws lambda create-function \
  --function-name agentcore-proxy \
  --runtime python3.11 \
  --handler proxy_handler.lambda_handler \
  --role arn:aws:iam::334107163417:role/lambda_role_himuro \
  --zip-file fileb:///tmp/agentcore-proxy.zip \
  --timeout 300 \
  --memory-size 128 \
  --environment "Variables={AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:ap-northeast-1:334107163417:runtime/CounselorSearchAI_counselor_search_agent-<RUNTIME_ID>}" \
  --region ap-northeast-1
```

### AgentCore Invoke 権限付与

```bash
aws iam put-role-policy \
  --role-name lambda_role_himuro \
  --policy-name AgentCoreInvokePolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "bedrock-agentcore:InvokeAgentRuntime",
        "Resource": "*"
      }
    ]
  }'
```

### 動作確認

```bash
echo '{"body": "{\"query\": \"test\"}"}' > /tmp/proxy-payload.json
aws lambda invoke \
  --function-name agentcore-proxy \
  --payload fileb:///tmp/proxy-payload.json \
  /tmp/proxy-response.json

cat /tmp/proxy-response.json | python3 -m json.tool
```

---

## API Gateway 設定

### REST API 作成

```bash
API_ID=$(aws apigateway create-rest-api \
  --name "CounselorSearchAgentCoreProxy" \
  --description "Proxy API for AgentCore Runtime" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' --output text)

ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID \
  --query 'items[0].id' --output text)
```

### POST メソッド・Lambda インテグレーション

```bash
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $ROOT_ID \
  --http-method POST \
  --authorization-type NONE

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $ROOT_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:ap-northeast-1:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-northeast-1:334107163417:function:agentcore-proxy/invocations"
```

### OPTIONS メソッド (CORS)

```bash
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $ROOT_ID \
  --http-method OPTIONS \
  --authorization-type NONE

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $ROOT_ID \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}'

aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $ROOT_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-models '{"application/json": "Empty"}' \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers": false, "method.response.header.Access-Control-Allow-Methods": false, "method.response.header.Access-Control-Allow-Origin": false}'

aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $ROOT_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key'"'"'", "method.response.header.Access-Control-Allow-Methods": "'"'"'OPTIONS,POST'"'"'", "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}'
```

### Lambda 呼び出し権限

```bash
aws lambda add-permission \
  --function-name agentcore-proxy \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:ap-northeast-1:334107163417:${API_ID}/*/*"
```

### デプロイ

```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### リソースポリシー (IP制限)

```bash
cat > /tmp/api-update.json << 'EOF'
{
  "restApiId": "API_ID",
  "patchOperations": [
    {
      "op": "replace",
      "path": "/policy",
      "value": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"execute-api:Invoke\",\"Resource\":\"arn:aws:execute-api:ap-northeast-1:334107163417:API_ID/*/*\"},{\"Effect\":\"Deny\",\"Principal\":\"*\",\"Action\":\"execute-api:Invoke\",\"Resource\":\"arn:aws:execute-api:ap-northeast-1:334107163417:API_ID/*/*\",\"Condition\":{\"NotIpAddress\":{\"aws:SourceIp\":\"39.110.219.164/32\"}}}]}"
    }
  ]
}
EOF

sed -i '' "s/API_ID/${YOUR_API_ID}/g" /tmp/api-update.json
aws apigateway update-rest-api --cli-input-json file:///tmp/api-update.json
```

---

## S3 Web Hosting デプロイ

### バケット作成・設定

```bash
# バケット作成
aws s3 mb s3://counselor-search-ai-frontend --region ap-northeast-1

# 静的ウェブサイトホスティング設定
aws s3 website s3://counselor-search-ai-frontend \
  --index-document index.html \
  --error-document index.html

# パブリックアクセスブロック解除
aws s3api put-public-access-block \
  --bucket counselor-search-ai-frontend \
  --public-access-block-configuration \
  BlockPublicAcls=false,IgnorePublicAcls=false,\
  BlockPublicPolicy=false,RestrictPublicBuckets=false

# バケットポリシー (IP制限)
aws s3api put-bucket-policy --bucket counselor-search-ai-frontend --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSpecificIP",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::counselor-search-ai-frontend/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "39.110.219.164/32"
        }
      }
    }
  ]
}'
```

### ビルド・アップロード

```bash
cd frontend
npm run build
aws s3 sync dist s3://counselor-search-ai-frontend --delete
```
