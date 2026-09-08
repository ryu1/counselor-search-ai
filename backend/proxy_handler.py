"""Proxy Lambda function for AgentCore Runtime.

Receives requests from the frontend and forwards them to the AgentCore Runtime.
"""

import json
import os
import boto3
import urllib.request
import urllib.error
from typing import Any, Dict

AGENTCORE_ENDPOINT = os.environ.get("AGENTCORE_ENDPOINT", "")
AGENTCORE_RUNTIME_ARN = os.environ.get("AGENTCORE_RUNTIME_ARN", "")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda 関数のエントリーポイント。

    フロントエンドからのリクエストを受け取り、AgentCore Runtime に転送する。
    """
    try:
        # リクエストボディを解析
        body = json.loads(event.get("body", "{}"))
        query = body.get("query", "")
        session_id = body.get("session_id")

        if not query:
            return _response(400, {"success": False, "error": {"message": "query is required"}})

        # AgentCore Runtime を呼び出し
        result = _invoke_agentcore(query, session_id)

        return _response(200, result)

    except Exception as e:
        return _response(500, {"success": False, "error": {"message": str(e)}})


def _invoke_agentcore(prompt: str, session_id: str = None) -> Dict[str, Any]:
    """AgentCore Runtime を呼び出す。"""
    import boto3
    import re

    # Runtime ARN からリージョンを抽出
    parts = AGENTCORE_RUNTIME_ARN.split(":")
    region = parts[3]

    client = boto3.client("bedrock-agentcore", region_name=region)

    # ペイロードにセッションIDを含める
    payload_data = {"prompt": prompt}

    # runtimeSessionId は33文字以上必要
    runtime_session_id = session_id if session_id and len(session_id) >= 33 else None

    invoke_kwargs = {
        "agentRuntimeArn": AGENTCORE_RUNTIME_ARN,
        "payload": json.dumps(payload_data).encode("utf-8"),
    }
    if runtime_session_id:
        invoke_kwargs["runtimeSessionId"] = runtime_session_id

    response = client.invoke_agent_runtime(**invoke_kwargs)

    # レスポンスを処理（StreamingBody に対応）
    response_body = response.get("response")
    if hasattr(response_body, "read"):
        payload = response_body.read()
    else:
        payload = response_body

    if isinstance(payload, bytes):
        raw_text = payload.decode("utf-8")
    else:
        raw_text = str(payload)

    # ストリーミングレスポンスからテキストを抽出
    # data: {"event": {"contentBlockDelta": {"delta": {"text": "..."}, ...}}} 形式
    text_parts = []
    response_session_id = None
    for line in raw_text.split("\n"):
        if line.startswith("data: "):
            try:
                event = json.loads(line[6:])
                delta = event.get("event", {}).get("contentBlockDelta", {}).get("delta", {})
                if "text" in delta:
                    text_parts.append(delta["text"])
                # セッションIDを抽出
                if "session_id" in event:
                    response_session_id = event["session_id"]
            except json.JSONDecodeError:
                pass

    answer = "".join(text_parts) if text_parts else raw_text

    # セッションIDをレスポンスに含める
    result = {
        "success": True,
        "result": {
            "answer": answer,
            "results": [],
        },
    }

    # セッションIDを設定
    if response_session_id:
        result["session_id"] = response_session_id
    elif session_id:
        result["session_id"] = session_id
    else:
        import uuid
        result["session_id"] = str(uuid.uuid4())

    return result


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """API Gateway 形式のレスポンスを生成する。"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }
