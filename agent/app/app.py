"""Counselor Search Agent for AgentCore Runtime.

Standard AgentCore implementation using BedrockAgentCoreApp + Strands Agent.
"""

import json
import os
from pathlib import Path
import boto3
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from model.load import load_model

app = BedrockAgentCoreApp()
log = app.logger

LAMBDA_FUNCTION_NAME = os.environ.get("LAMBDA_FUNCTION_NAME", "search_counselors")
MEMORY_ID = os.environ.get("AGENTCORE_MEMORY_ID", "")

SYSTEM_PROMPT_PATH = Path(__file__).parent / "system-prompt.md"


def _load_system_prompt() -> str:
    """system-prompt.md からシステムプロンプトを読み込む。"""
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.warning(f"System prompt not found at {SYSTEM_PROMPT_PATH}, using fallback")
        return "あなたはカウンセラー検索アシスタントです。search_counselors ツールを使って検索してください。"

_lambda_client = None


def _get_lambda_client():
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda")
    return _lambda_client


@tool
def search_counselors(
    stations: list[str] = [],
    area_of_expertise: list[str] = [],
    methods: list[str] = [],
    genders: list[str] = [],
    ages: list[str] = [],
    requested_datetime: str = None,
    datetime_from: str = None,
    datetime_to: str = None,
) -> str:
    """カウンセラー検索ツール。ユーザーの希望条件に合致するカウンセリング事務所を検索します。

    Args:
        stations: 最寄駅のリスト（例: ["新宿駅"]）。マスター値: 新宿駅, 立川駅, 池袋駅, 渋谷駅, 品川駅, 東京駅, 秋葉原駅, 中野駅, 吉祥寺駅, 水道橋駅, 溜池山王駅, 新橋駅, ほか
        area_of_expertise: 専門分野のリスト（例: ["うつ"]）。マスター値: うつ, 不安, 人間関係, ストレス, 依存, 家族, 仕事, 子育て, デート, 結婚, 離婚, 介護, 心身の調子, パニック, PTSD, 摂食障害, むけ, コミュニケーション, キャリア, ほか
        methods: 相談方法のリスト（例: ["オンライン"]）。マスター値: オンライン, 対面, 電話, メール
        genders: カウンセラーの性別のリスト（例: ["女性"]）。マスター値: 男性, 女性
        ages: カウンセラーの年代のリスト（例: ["30代"]）。マスター値: 20代, 30代, 40代, 50代, 60代以上
        requested_datetime: 希望日時（ISO 8601形式: 2026-09-12T10:00）
        datetime_from: 検索開始日時（ISO 8601形式: 2026-09-12T10:00）
        datetime_to: 検索終了日時（ISO 8601形式: 2026-09-12T11:00）
    """
    parameters = {
        "stations": stations,
        "area_of_expertise": area_of_expertise,
        "methods": methods,
        "genders": genders,
        "ages": ages,
        "requested_datetime": requested_datetime,
        "datetime_from": datetime_from,
        "datetime_to": datetime_to,
    }

    try:
        client = _get_lambda_client()
        response = client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps({"parameters": parameters}),
        )
        payload = json.loads(response["Payload"].read().decode("utf-8"))

        if payload.get("success"):
            result = payload["result"]
            count = result["count"]
            offices = result["results"]

            lines = [f"該当する事務所を {count} 件見つけました。"]
            for i, office in enumerate(offices, 1):
                lines.append(f"\n{i}. {office['office_name']}")
                if office.get("nearest_stations"):
                    lines.append(f"   最寄駅: {', '.join(office['nearest_stations'])}")
                if office.get("matched_counselors"):
                    for c in office["matched_counselors"]:
                        lines.append(f"   カウンセラー: {c['name']}")
            return "\n".join(lines)
        else:
            error = payload.get("error", {})
            return f"検索エラー: {error.get('message', '不明なエラー')}"
    except Exception as e:
        return f"処理中にエラーが発生しました: {str(e)}"


def process_prompt(prompt):
    """GenU が送る prompt（ContentBlock 配列）からテキストを抽出する。"""
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        texts = [block["text"] for block in prompt if isinstance(block, dict) and "text" in block]
        return "\n".join(texts) if texts else ""
    return str(prompt)


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")

    prompt = process_prompt(payload.get("prompt", ""))
    session_id = context.session_id

    log.info(f"[AGENT] session_id: {session_id}")
    log.info(f"[AGENT] prompt: {prompt[:100]}...")

    # Actor ID を生成（ユーザーごとに一意）
    actor_id = f"actor_{session_id}"

    # AgentCore Memory Session Manager を作成
    config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=session_id,
        actor_id=actor_id,
        batch_size=10,
    )

    log.info(f"[AGENT] memory_id: {MEMORY_ID}")
    log.info(f"[AGENT] actor_id: {actor_id}")

    with AgentCoreMemorySessionManager(config, region_name="ap-northeast-1") as session_manager:
        agent = Agent(
            model=load_model(),
            system_prompt=_load_system_prompt(),
            tools=[search_counselors],
            session_manager=session_manager,
        )

        async for event in agent.stream_async(prompt):
            if "event" in event:
                yield event


if __name__ == "__main__":
    app.run()
