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


def create_mcp_client():
    """AgentCore Gateway MCP エンドポイントへの MCPClient を作成する（SigV4認証付き）。"""
    import httpx
    import botocore.auth
    import botocore.awsrequest
    import botocore.session
    from strands.tools.mcp.mcp_client import MCPClient
    from mcp.client.streamable_http import streamable_http_client

    # Gateway URL に /mcp を付与して MCP エンドポイントとする
    base_url = os.environ.get(
        "BOOKING_GATEWAY_URL",
        "https://counselorsearchai-booking-api-gateway-rlkzu5smxq.gateway.bedrock-agentcore.ap-northeast-1.amazonaws.com",
    )
    mcp_url = f"{base_url.rstrip('/')}/mcp"

    # Create botocore session and signer for SigV4
    bc_session = botocore.session.get_session()
    credentials = bc_session.get_credentials()
    signer = botocore.auth.SigV4Auth(credentials, "bedrock-agentcore", "ap-northeast-1")

    # Create a custom httpx client with SigV4 signing
    class SigV4Auth(httpx.Auth):
        def __init__(self, signer):
            self.signer = signer

        def auth_flow(self, request):
            aws_request = botocore.awsrequest.AWSRequest(
                method=request.method,
                url=str(request.url),
                headers=dict(request.headers),
                data=request.content,
            )
            self.signer.add_auth(aws_request)
            request.headers.update(dict(aws_request.headers))
            yield request

    # Create httpx client with SigV4 auth
    http_client = httpx.AsyncClient(auth=httpx.BasicAuth("","") if False else SigV4Auth(
        botocore.auth.SigV4Auth(
            botocore.session.get_session().get_credentials(),
            "bedrock-agentcore",
            "ap-northeast-1"
        )
    ), timeout=30.0)

    # Strands の公式 MCPClient を使用（認証付き HTTP クライアントで）
    return MCPClient(lambda: streamable_http_client(
        "https://counselorsearchai-booking-api-gateway-rlkzu5smxq.gateway.bedrock-agentcore.ap-northeast-1.amazonaws.com/mcp",
        http_client=http_client
    ))


async def create_agent_with_mcp_tools(session_manager):
    """MCP Gateway ツールを含む Agent を作成する。"""
    mcp_client = create_mcp_client()

    # Strands Agent 用のツールリストを構築
    tools = [search_counselors]

    # MCP Gateway からツールを自動変換して取得（load_tools は async で AgentTool を返す）
    mcp_tools = await mcp_client.load_tools()
    tools.extend(mcp_tools)

    agent = Agent(
        model=load_model(),
        system_prompt=_load_system_prompt(),
        tools=tools,
        session_manager=session_manager,
    )
    return agent


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
    actor_id = payload.get("actor_id", "default_actor")

    log.info(f"[AGENT] session_id: {session_id}")
    log.info(f"[AGENT] actor_id: {actor_id}")
    log.info(f"[AGENT] prompt: {prompt[:100]}...")
    log.info(f"[AGENT] memory_id: {MEMORY_ID}")

    # AgentCore Memory Session Manager を作成
    config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=session_id,
        actor_id=actor_id,
        batch_size=10,
    )

    try:
        with AgentCoreMemorySessionManager(config, region_name="ap-northeast-1") as session_manager:
            agent = await create_agent_with_mcp_tools(session_manager)

            async for event in agent.stream_async(prompt):
                if "event" in event:
                    yield event
    except Exception as e:
        log.error(f"[AGENT] Error: {str(e)}")
        raise


if __name__ == "__main__":
    app.run()