# カウンセラー検索AIデモ

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-green?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20Athena%20%7C%20Bedrock-orange?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![AgentCore](https://img.shields.io/badge/AgentCore-Runtime-purple?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/agentcore/)

> 自然言語で相談希望を入力するだけで、AIが条件を理解し、カウンセリングオフィスを検索・提示するデモシステム

## アプリケーション概要・特長

- **自然言語チャット入力** — フォーム指定なし、会話形式で条件を伝える
- **日時表現の正規化** — 「明日」「来週土曜日」「9/12」「14時ごろ」等に対応
- **条件不足時の追加質問** — 必須条件が不足している場合のみ質問
- **Athena SQL検索** — S3上のJSONLデータをサーバーレスで検索
- **オフィス単位の結果表示** — マッチしたカウンセラーを含むオフィスリスト

## 設計ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [product.md](docs/product.md) | プロダクト要件・ユーザーストーリー・機能一覧 |
| [architecture.md](docs/architecture.md) | システム構成・データモデル・コンポーネント設計 |
| [design.md](docs/design.md) | GUIデザイン・カラーパレット・コンポーネント仕様 |
| [api.md](docs/api.md) | API仕様・Tool入出力スキーマ・エラーコード |
| [tech.md](docs/tech.md) | 技術選定・ライブラリバージョン・パフォーマンス要件 |
| [conventions.md](docs/conventions.md) | コーディング規約・Git規約・セットアップ手順 |
| [security.md](docs/security.md) | セキュリティ設計・脅威モデル・IAM設計 |
| [operations.md](docs/operations.md) | 運用手順・障害対応・クリーンアップ |
| [review.md](docs/review.md) | レビュー方針・チェックリスト |
| [glossary.md](docs/glossary.md) | ユビキタス言語・英日対応表 |
| [lambda-deployment.md](docs/lambda-deployment.md) | Lambdaデプロイ手順（AWS CLI） |

## ライセンス

個人利用・学習目的のデモプロジェクトです
