"""Search result aggregator.

Converts Athena query row data into office-unit search results
with matched counselors information.
"""

import json
from typing import Any, Dict, List, Optional


class CounselorMatch:
    """Represents a counselor matching the search criteria."""

    def __init__(
        self,
        name: str,
        gender: str,
        age: str,
        methods: List[str],
        area_of_expertise: List[str],
    ):
        self.name = name
        self.gender = gender
        self.age = age
        self.methods = methods or []
        self.area_of_expertise = area_of_expertise or []


class OfficeResult:
    """Represents a counseling office matching the search criteria."""

    def __init__(
        self,
        office_id: str,
        office_name: str,
        nearest_stations: List[str],
        matched_counselors: List[CounselorMatch],
    ):
        self.office_id = office_id
        self.office_name = office_name
        self.nearest_stations = nearest_stations or []
        self.matched_counselors = matched_counselors or []


def _parse_array_value(value: str) -> List[str]:
    """Athena から返される配列文字列をリストに変換する。

    Athena は配列を "[value1,value2]" や [value1,value2] のような文字列で返す。
    JSON パースで正しいリストに変換する。パースに失敗した場合は角括弧を除去する。

    Args:
        value: Athena から返される配列文字列

    Returns:
        文字列リスト
    """
    if not value:
        return []

    # 既にリストの場合はそのまま返す
    if isinstance(value, list):
        return value

    # 文字列の場合、JSON パースを試行
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except (json.JSONDecodeError, TypeError):
        pass

    # JSON パースに失敗した場合、角括弧を除去して分割
    # "[value1,value2]" や [value1,value2] 形式に対応
    stripped = value.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if not inner:
            return []
        # カンマで分割し、各値の余計なクォートを除去
        items = []
        for item in inner.split(","):
            item = item.strip()
            # クォートで囲まれている場合は除去
            if (item.startswith('"') and item.endswith('"')) or \
               (item.startswith("'") and item.endswith("'")):
                item = item[1:-1]
            items.append(item)
        return items

    # 単一値として返す
    return [value]


def _parse_athena_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Athena GetQueryResults の行データを辞書リストに変換する。

    Athena の行形式: [{"Data": [{"VarCharValue": "col1"}, {"VarCharValue": "val1"}]}, ...]
    最初の行はヘッダー。

    Args:
        rows: Athena GetQueryResults の行データリスト

    Returns:
        カラム名をキーとした辞書のリスト
    """
    if len(rows) < 2:
        return []

    # 最初の行はヘッダー
    headers = [col.get("VarCharValue", "") for col in rows[0].get("Data", [])]

    # 2行目以降はデータ
    result = []
    for row in rows[1:]:
        values = [col.get("VarCharValue", "") for col in row.get("Data", [])]
        if len(values) == len(headers):
            result.append(dict(zip(headers, values)))

    return result


def aggregate_results(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Athenaクエリ結果を行データからオフィス単位で集約する。

    Args:
        rows: Athenaクエリからの行データリスト

    Returns:
        集約された検索結果辞書
    """
    offices: Dict[str, OfficeResult] = {}

    # Athena の行形式を辞書リストに変換
    data_rows = _parse_athena_rows(rows)

    for row in data_rows:
        office_id = row.get("office_id")
        office_name = row.get("office_name")

        if office_id not in offices:
            nearest_stations_str = row.get("nearest_stations", "")
            offices[office_id] = OfficeResult(
                office_id=office_id,
                office_name=office_name or "",
                nearest_stations=_parse_array_value(nearest_stations_str),
                matched_counselors=[],
            )

        # Extract counselor data from the row
        counselor_name = row.get("counselor_name")
        counselor_gender = row.get("gender")
        counselor_age = row.get("age")
        counselor_method = row.get("method", "")
        counselor_expertise = row.get("area_of_expertise", "")

        if counselor_name:
            counselor_match = CounselorMatch(
                name=counselor_name,
                gender=counselor_gender or "",
                age=counselor_age or "",
                methods=_parse_array_value(counselor_method),
                area_of_expertise=_parse_array_value(counselor_expertise),
            )
            offices[office_id].matched_counselors.append(counselor_match)

    # Convert to output format
    results = [
        {
            "office_id": office.office_id,
            "office_name": office.office_name,
            "nearest_stations": office.nearest_stations,
            "matched_counselors": [
                {
                    "name": c.name,
                    "gender": c.gender,
                    "age": c.age,
                    "methods": c.methods,
                    "area_of_expertise": c.area_of_expertise,
                }
                for c in office.matched_counselors
            ],
        }
        for office in offices.values()
    ]

    return {
        "count": len(results),
        "results": results,
    }