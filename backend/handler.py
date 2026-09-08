"""Lambda function handler for search_counselors Tool.

Entry point called by AgentCore Runtime.
Processes search conditions, validates, generates SQL, executes Athena query,
and returns aggregated results.
"""

import json
import os
from typing import Any, Dict, List

import boto3

from validator import validate_and_raise
from sql_builder import build_search_sql, build_datetime_sql
from aggregator import aggregate_results, OfficeResult, CounselorMatch
from models import SearchConditions, SearchResult, DateTimeCondition


# Athena client (global for reuse across invocations)
_athena_client = None


def _get_athena_client() -> Any:
    """Athena クライアントの遅延初期化"""
    global _athena_client
    if _athena_client is None:
        _athena_client = boto3.client("athena")
    return _athena_client


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda関数のエントリーポイント。

    エージェントからの Tool 呼び出しを受け取り、検索を実行して結果を返す。

    Args:
        event: AgentCore Tool invocation event containing search conditions
        context: Lambda execution context

    Returns:
        Tool result dict with search results or error information
    """
    try:
        # 1. 条件の抽出と検証
        parameters = event.get("parameters", {})
        validate_and_raise(parameters)

        # 2. SearchConditions オブジェクトに変換
        conditions = _parse_conditions(parameters)

        # 3. SQL の生成
        sql = build_search_sql(parameters)
        datetime_sql = build_datetime_sql(conditions.requested_datetime)
        if datetime_sql and sql != "SELECT 1 FROM counseling_demo.offices o LIMIT 0":
            sql = f"{sql} AND {datetime_sql}"

        # 4. Athena クエリの実行
        query_id = _execute_athena_query(sql)

        # 5. 結果の取得と集約
        result_rows = _get_query_results(query_id)
        aggregated = aggregate_results(result_rows)

        # 6. レスポンス成形
        return _build_tool_result(aggregated)

    except ValueError as e:
        # バリデーションエラー（マスター値チェックなど）
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "invalid_fields": [],
            },
        }
    except Exception as e:
        # その他のエラー
        return {
            "success": False,
            "error": {
                "code": "ATHENA_ERROR",
                "message": "検索処理で一時的な問題が発生しました。",
                "details": str(e),
            },
        }


def _parse_conditions(parameters: dict[str, Any]) -> SearchConditions:
    """Tool 入力パラメータを SearchConditions オブジェクトに変換。

    Args:
        parameters: Agent から受け取ったパラメータ辞書

    Returns:
        SearchConditions オブジェクト
    """
    stations = parameters.get("stations", [])
    expertise = parameters.get("area_of_expertise", [])
    methods = parameters.get("methods", [])
    genders = parameters.get("genders", [])
    ages = parameters.get("ages", [])
    requested_datetime = parameters.get("requested_datetime")
    datetime_from = parameters.get("datetime_from")
    datetime_to = parameters.get("datetime_to")

    # datetime_from/datetime_to が指定されている場合は、requested_datetime に変換
    if datetime_from or datetime_to:
        requested_datetime = {
            "start": datetime_from,
            "end": datetime_to,
        }

    return SearchConditions(
        stations=stations,
        area_of_expertise=expertise,
        methods=methods,
        genders=genders,
        ages=ages,
        requested_datetime=requested_datetime,
    )


def _execute_athena_query(sql: str) -> str:
    """Athena クエリを実行し、クエリ実行 ID を返す。

    Args:
        sql: 実行する SQL クエリ文字列

    Returns:
        クエリ実行 ID
    """
    client = _get_athena_client()
    data_bucket = os.environ.get("DATA_BUCKET", "counselor-search-ai-data")
    result_bucket = os.environ.get("ATHENA_RESULTS_BUCKET", "counselor-search-ai-athena-results")
    workgroup = os.environ.get("ATHENA_WORKGROUP", "counseling-demo-wg")

    response = client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": "counseling_demo_db"},
        WorkGroup=workgroup,
    )

    return response["QueryExecutionId"]


def _get_query_results(query_id: str) -> List[Dict[str, Any]]:
    """Athena クエリの実行結果をポーリングして取得する。

    Args:
        query_id: クエリ実行 ID

    Returns:
        行データのリスト
    """
    client = _get_athena_client()

    # クエリ完了待ち（ポーリング）
    max_attempts = 30
    for attempt in range(max_attempts):
        response = client.get_query_execution(QueryExecutionId=query_id)
        status = response["QueryExecution"]["Status"]["State"]

        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            if status == "SUCCEEDED":
                # 結果取得
                results_response = client.get_query_results(
                    QueryExecutionId=query_id, MaxResults=1000
                )
                return results_response["ResultSet"]["Rows"]
            else:
                return []

        # 待機（指数バックオフ）
        import time
        time.sleep(0.5 * (attempt + 1))

    # タイムアウト
    return []


def _build_tool_result(aggregated: dict[str, Any]) -> dict[str, Any]:
    """Tool結果をエージェントに返却する形式に整形する。

    Args:
        aggregated: 集約関数によって返された辞書

    Returns:
        エージェントへ返却する Tool 結果辞書
    """
    return {
        "success": True,
        "result": {
            "count": aggregated.get("count", 0),
            "results": aggregated.get("results", []),
        },
    }