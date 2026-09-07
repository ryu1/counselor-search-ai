# API設計書：カウンセラー検索AIデモ

## 1. 概要

本システムのAPI通信は以下の2経路で構成される：

1. **フロントエンド ↔ AgentCore Runtime** — ユーザー会話の送受信
2. **Agent ↔ Lambda (Tool)** — 検索ツールの呼び出し・結果取得

---

## 2. フロントエンド → AgentCore Runtime

### 2.1 エンドポイント

AgentCore Runtimeのデフォルトエンドポイントを使用：

```
POST https://<agentcore-endpoint>.bedrock-agentcore.<region>.amazonaws.com/invocations
```

※ CloudFormationで作成されるAgentCore RuntimeエンドポイントURLを環境変数で注入

### 2.2 リクエスト

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token>  // デモ用は未実装・将来Cognito対応時追加
X-Session-Id: <uuid>           // 会話セッション識別子
X-Current-Datetime: <ISO8601>  // 現在日時 (Asia/Tokyo) 例: 2026-09-03T08:30:00+09:00
X-Timezone: Asia/Tokyo
```

**Body:**
```json
{
  "message": "新宿駅で女性のカウンセラーにオンラインで土曜の14時ごろ相談したい",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| message | string | Yes | ユーザー入力メッセージ (1-2000文字) |
| session_id | string | Yes | セッションID (UUID v4) 初回はフロントで生成 |

### 2.3 レスポンス

**Success (200):**
```json
{
  "response": "承知しました。土曜14時ごろですね。相談したい内容（専門領域）はありますか？",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "question",
  "extracted_conditions": {
    "stations": ["新宿駅"],
    "genders": ["女性"],
    "methods": ["オンライン"],
    "requested_datetime": {
      "day_of_week": "Saturday",
      "around": "14:00",
      "tolerance_minutes": 60
    }
  }
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| response | string | AI生成応答メッセージ (Markdown可) |
| session_id | string | 同一セッションID |
| status | enum | `question` (追加質問) / `searching` (検索中) / `result` (結果表示) / `error` |
| extracted_conditions | object | 抽出済み検索条件（フロント表示用・任意） |

**Error (4xx/5xx):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "メッセージが空です",
    "details": {}
  }
}
```

### 2.4 ステータスコード

| コード | 条件 |
|-------|------|
| 200 | 正常応答 |
| 400 | リクエスト不正 (message欠落・session_id不正等) |
| 401 | 認証エラー (将来実装時) |
| 429 | レート制限超過 |
| 500 | AgentCore内部エラー |
| 503 | AgentCore利用不可・メンテナンス中 |

### 2.5 タイムアウト・リトライ

| 設定 | 値 |
|------|-----|
| 接続タイムアウト | 5秒 |
| 応答タイムアウト | 60秒 (Agent思考・Tool実行含む) |
| リトライ | 最大2回 (指数バックオフ 1s, 2s) |
| リトライ対象 | 5xx, 429, ネットワークエラー |

---

## 3. Agent → Lambda (Tool: search_counselors)

### 3.1 Tool定義 (AgentCore Tool Schema)

```json
{
  "name": "search_counselors",
  "description": "指定された条件に一致するカウンセリングオフィスとカウンセラーを検索する",
  "parameters": {
    "type": "object",
    "properties": {
      "stations": {
        "type": "array",
        "items": { "type": "string" },
        "description": "最寄り駅 (マスター値のみ)"
      },
      "area_of_expertise": {
        "type": "array",
        "items": { "type": "string" },
        "description": "専門領域 (マスター値のみ)"
      },
      "methods": {
        "type": "array",
        "items": { "type": "string" },
        "description": "カウンセリング方法 (マスター値のみ)"
      },
      "genders": {
        "type": "array",
        "items": { "type": "string" },
        "description": "性別 (マスター値のみ)"
      },
      "ages": {
        "type": "array",
        "items": { "type": "string" },
        "description": "年代 (マスター値のみ)"
      },
      "requested_datetime": {
        "type": ["object", "null"],
        "properties": {
          "start": { "type": "string", "format": "date-time" },
          "end": { "type": "string", "format": "date-time" },
          "day_of_week": { "type": "string", "enum": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"] },
          "around": { "type": "string", "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$" },
          "tolerance_minutes": { "type": "integer", "minimum": 0, "maximum": 180 }
        },
        "description": "相談希望日時 (絶対日時または曜日+時間幅)"
      }
    },
    "required": ["stations", "area_of_expertise", "methods", "genders", "ages", "requested_datetime"],
    "additionalProperties": false
  }
}
```

### 3.2 Lambda入力イベント (AgentCore Tool Invocation)

```json
{
  "tool_name": "search_counselors",
  "parameters": {
    "stations": ["新宿駅"],
    "area_of_expertise": ["不安"],
    "methods": ["オンライン"],
    "genders": ["女性"],
    "ages": [],
    "requested_datetime": {
      "day_of_week": "Saturday",
      "around": "14:00",
      "tolerance_minutes": 60
    }
  },
  "invocation_id": "inv-abc123",
  "agent_session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 3.3 Lambda出力 (Tool Result)

**Success:**
```json
{
  "success": true,
  "result": {
    "count": 2,
    "results": [
      {
        "office_id": "36930",
        "office_name": "メンタルサポート新宿",
        "nearest_stations": ["渋谷駅", "池袋駅"],
        "matched_counselors": [
          {
            "name": "鈴木 美咲",
            "gender": "女性",
            "age": "30代",
            "methods": ["オンライン", "電話"],
            "area_of_expertise": ["不安", "うつ"]
          }
        ]
      },
      {
        "office_id": "36945",
        "office_name": "こころの相談室渋谷",
        "nearest_stations": ["渋谷駅"],
        "matched_counselors": [
          {
            "name": "田中 優子",
            "gender": "女性",
            "age": "40代",
            "methods": ["オンライン", "対面"],
            "area_of_expertise": ["対人関係", "ストレス"]
          }
        ]
      }
    ]
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "無効な駅名が含まれています: '存在しない駅'",
    "invalid_fields": ["stations"]
  }
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| success | boolean | 成否 |
| result | object | 検索結果 (success=true時) |
| error | object | エラー詳細 (success=false時) |
| error.code | string | `VALIDATION_ERROR` / `ATHENA_ERROR` / `TIMEOUT` / `INTERNAL_ERROR` |
| error.message | string | ユーザー向けではない内部メッセージ |
| error.invalid_fields | string[] | バリデーションエラー時の対象フィールド |

---

## 4. マスターデータ定義 (Agent・Lambda共通参照)

以下の値のみを検索条件として受け付ける。Agent・Lambda両方で同一マスターを保持。

### 4.1 stations (駅マスター)

```json
[
  "新宿駅", "立川駅", "池袋駅", "渋谷駅", "品川駅", "東京駅",
  "秋葉原駅", "中野駅", "吉祥寺駅", "水道橋駅", "溜池山王駅",
  "新橋駅", "ほか"
]
```

### 4.2 area_of_expertise (専門領域マスター)

```json
[
  "うつ", "不安", "人間関係", "ストレス", "依存", "家族",
  "仕事", "子育て", "デート", "結婚", "離婚", "介護",
  "心身の調子", "パニック", "PTSD", "摂食障害", "むけ",
  "コミュニケーション", "キャリア", "ほか"
]
```

### 4.3 methods (カウンセリング方法マスター)

```json
["オンライン", "対面", "電話", "メール"]
```

### 4.4 genders (性別マスター)

```json
["男性", "女性"]
```

### 4.5 ages (年代マスター)

```json
["20代", "30代", "40代", "50代", "60代以上"]
```

---

## 5. Lambda → Athena (内部SQL)

### 5.1 実行API

```
POST https://athena.<region>.amazonaws.com/
Action=StartQueryExecution
QueryString=<SQL>
WorkGroup=counseling-demo-wg
ResultConfiguration.OutputLocation=s3://<result-bucket>/query-results/
```

### 5.2 ポーリング

```
GET https://athena.<region>.amazonaws.com/
Action=GetQueryExecution
QueryExecutionId=<id>
```
- 間隔: 0.5秒 → 1秒 → 2秒 (指数バックオフ)
- 最大待機: 5分 (300秒)
- 状態: `QUEUED` → `RUNNING` → `SUCCEEDED` | `FAILED` | `CANCELLED`

### 5.3 結果取得

```
GET https://athena.<region>.amazonaws.com/
Action=GetQueryResults
QueryExecutionId=<id>
MaxResults=1000
NextToken=<token>  // ページネーション
```

---

## 6. エラーコード一覧

| コード | HTTP | 発生箇所 | ユーザー向けメッセージ例 |
|-------|------|---------|------------------------|
| VALIDATION_ERROR | 400 | Lambda入力 | 入力条件に誤りがあります |
| MASTER_VALUE_NOT_FOUND | 400 | Lambda入力 | 指定された値が見つかりません |
| ATHENA_QUERY_FAILED | 500 | Athena実行 | 検索処理でエラーが発生しました |
| ATHENA_TIMEOUT | 504 | Athenaポーリング | 検索に時間がかかりすぎています |
| INTERNAL_ERROR | 500 | Lambda内部 | 一時的なエラーが発生しました |
| AGENT_ERROR | 500 | AgentCore | AI処理でエラーが発生しました |
| RATE_LIMITED | 429 | AgentCore/API | アクセスが集中しています。少し待ってからお試しください |

---

## 7. バージョニング・互換性

- Toolスキーマ変更時は `search_counselors_v2` 等の新Tool名で追加し、旧版はDeprecated扱い
- フロントエンド↔AgentCore間は `X-API-Version` ヘッダーで将来管理 (現状 v1 固定)
- 破壊的変更は新エンドポイント・新Tool名で並行運用後切替

---

## 8. 開発・テスト用モック

### 8.1 Lambdaローカル実行用イベント例

```json
// test/events/search-valid.json
{
  "tool_name": "search_counselors",
  "parameters": {
    "stations": ["新宿駅"],
    "area_of_expertise": [],
    "methods": ["オンライン"],
    "genders": ["女性"],
    "ages": [],
    "requested_datetime": {
      "start": "2026-09-04T14:00:00+09:00",
      "end": "2026-09-04T15:00:00+09:00"
    }
  }
}
```

### 8.2 フロントエンド開発用モックサーバー (MSW)

```typescript
// mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.post('/invocations', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      response: `モック応答: "${body.message}"を受信しました`,
      session_id: body.session_id,
      status: 'result',
      extracted_conditions: {}
    })
  })
]
```