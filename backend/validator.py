"""Validator for search_counselors Tool input.

Validates that all search conditions use master-approved values only.
Raises ValueError if any invalid values are detected.
"""

from typing import Any

# Master data - these are the only values accepted for search conditions.
# Master values for validation

MASTER_STATIONS = frozenset([
    "新宿駅", "立川駅", "池袋駅", "渋谷駅", "品川駅", "東京駅",
    "秋葉原駅", "中野駅", "吉祥寺駅", "水道橋駅", "溜池山王駅",
    "新橋駅", "ほか",
])

MASTER_EXPERTISE = frozenset([
    "うつ", "不安", "人間関係", "ストレス", "依存", "家族",
    "仕事", "子育て", "デート", "結婚", "離婚", "介護",
    "心身の調子", "パニック", "PTSD", "摂食障害", "むけ",
    "コミュニケーション", "キャリア", "ほか",
])

MASTER_METHODS = frozenset(["オンライン", "対面", "電話", "メール"])

MASTER_GENDERS = frozenset(["男性", "女性"])

MASTER_AGES = frozenset(["20代", "30代", "40代", "50代", "60代以上"])


def escape_sql(value: str) -> str:
    """SQLインジェクション対策のエスケープ"""
    return value.replace("'", "''")


def validate_conditions(conditions: dict[str, Any]) -> list[str]:
    """検索条件を検証し、問題があるフィールドのリストを返す。

    マスター値以外のパラメータ（requested_datetimeなど）についての
    詳細なフォーマットチェックは行わず、存在するかのチェックのみ行います。

    Returns:
        リスト of invalid field names (empty list if all valid)
    """
    invalid_fields: list[str] = []

    # stations validation
    stations = conditions.get("stations", [])
    for station in stations:
        if station not in MASTER_STATIONS:
            invalid_fields.append("stations")
            break  # Only add once per field

    # area_of_expertise validation
    expertise = conditions.get("area_of_expertise", [])
    for field in expertise:
        if field not in MASTER_EXPERTISE:
            invalid_fields.append("area_of_expertise")
            break  # Only add once per field

    # methods validation
    methods = conditions.get("methods", [])
    for method in methods:
        if method not in MASTER_METHODS:
            invalid_fields.append("methods")
            break

    # genders validation
    genders = conditions.get("genders", [])
    for gender in genders:
        if gender not in MASTER_GENDERS:
            invalid_fields.append("genders")
            break

    # ages validation
    ages = conditions.get("ages", [])
    for age in ages:
        if age not in MASTER_AGES:
            invalid_fields.append("ages")
            break

    # requested_datetime: only check that it exists, not the format
    # (format normalization is handled separately in condition extraction)
    if "requested_datetime" not in conditions:
        invalid_fields.append("requested_datetime")

    return invalid_fields


def validate_and_raise(conditions: dict[str, Any]) -> None:
    """条件を検証し、問題があれば例外を発生させる。

    Raises:
        ValueError: 無効なフィールドが含まれる場合
    """
    invalid = validate_conditions(conditions)
    if invalid:
        raise ValueError(
            f"検索条件の検証に失敗しました: {', '.join(set(invalid))}. "
            "マスター値に存在しない値が含まれています。"
        )