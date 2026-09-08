from typing import Any, Dict, List, Optional


def escape_sql(value: str) -> str:
    """SQLシングルクォートエスケープ"""
    return value.replace("'", "''")


def build_search_sql(conditions: dict[str, Any]) -> str:
    """検索条件からAthena SQLクエリを構築する。

    ルール:
    - 同一項目内は OR
    - 項目間は AND
    - offices と counselors を JOIN して検索

    Args:
        conditions: SearchConditions dict from Lambda event

    Returns:
        Athena実行用の SQL クエリ文字列
    """
    office_clauses: List[str] = []
    counselor_clauses: List[str] = []

    # 1. 駅検索 → offices テーブル
    stations = conditions.get("stations", [])
    if stations:
        # 「ほか」または「指定なし」は全駅マッチ（フィルタなし）
        if "ほか" not in stations and "指定なし" not in stations:
            station_conditions = []
            for s in stations:
                s_escaped = escape_sql(s)
                station_conditions.append("contains(o.nearest_stations, '" + s_escaped + "')")
            office_clauses.append("(" + " OR ".join(station_conditions) + ")")

    # 2. 専門領域検索 → counselors テーブル
    expertise = conditions.get("area_of_expertise", [])
    if expertise:
        # 「ほか」または「指定なし」は全領域マッチ（フィルタなし）
        if "ほか" not in expertise and "指定なし" not in expertise:
            expertise_conditions = []
            for e in expertise:
                e_escaped = escape_sql(e)
                expertise_conditions.append("contains(c.area_of_expertise, '" + e_escaped + "')")
            counselor_clauses.append("(" + " OR ".join(expertise_conditions) + ")")

    # 3. カウンセリング方法検索 → counselors テーブル
    methods = conditions.get("methods", [])
    if methods:
        # 「ほか」または「指定なし」は全方法マッチ（フィルタなし）
        if "ほか" not in methods and "指定なし" not in methods:
            method_conditions = []
            for m in methods:
                m_escaped = escape_sql(m)
                method_conditions.append("contains(c.method, '" + m_escaped + "')")
            counselor_clauses.append("(" + " OR ".join(method_conditions) + ")")

    # 4. 性別検索 → counselors テーブル
    genders = conditions.get("genders", [])
    if genders:
        # 「指定なし」は全性別マッチ（フィルタなし）
        if "指定なし" not in genders:
            gender_items = ", ".join(["'" + g + "'" for g in genders])
            counselor_clauses.append("c.gender IN (" + gender_items + ")")

    # 5. 年代検索 → counselors テーブル
    ages = conditions.get("ages", [])
    if ages:
        # 「指定なし」は全年代マッチ（フィルタなし）
        if "指定なし" not in ages:
            age_items = ", ".join(["'" + a + "'" for a in ages])
            counselor_clauses.append("c.age IN (" + age_items + ")")

    # WHERE 句の組み立て
    all_clauses = office_clauses + counselor_clauses

    if not all_clauses:
        return "SELECT 1 FROM counseling_demo_db.offices o LIMIT 0"

    where_clause = " AND ".join(all_clauses)
    return (
        "SELECT o.id AS office_id, o.office_name, o.nearest_stations, "
        "c.office_id AS counselor_office_id, c.name AS counselor_name, "
        "c.area_of_expertise, c.method, c.gender, c.age "
        "FROM counseling_demo_db.offices o "
        "JOIN counseling_demo_db.counselors c ON o.id = c.office_id "
        "WHERE " + where_clause
    )


def build_datetime_sql(datetime_cond: Any) -> Optional[str]:
    """相談希望日時に対する営業時間フィルタリング SQL を構築。

    Args:
        datetime_conditions: requested_datetime の中身（dict または文字列）

    Returns:
        Athena 用の営業時間フィルタリング SQL 文字列、または None
    """
    if isinstance(datetime_cond, str):
        return None

    datetime_cond: dict[str, Any] = datetime_cond or {}
    day_of_week = datetime_cond.get("day_of_week")
    start = datetime_cond.get("start")
    end = datetime_cond.get("end")

    if start and end:
        # datetime_from/datetime_to 形式の処理
        start_str = start.replace("T", " ").split("+")[0] if "+" in start else start.replace("T", " ")
        end_str = end.replace("T", " ").split("+")[0] if "+" in end else end.replace("T", " ")
        start_time = start_str.split()[-1] if " " in start_str else "14:00"
        end_time = end_str.split()[-1] if " " in end_str else "15:00"
        return (
            "EXISTS ("
            "SELECT 1 "
            "FROM UNNEST(o.opening_hours_specification) AS t(day) "
            "WHERE "
            "CAST(day.opens AS TIME) <= TIME '" + end_time + ":00' "
            "AND CAST(day.closes AS TIME) >= TIME '" + start_time + ":00:00'"
            ")"
        )
    elif day_of_week:
        return (
            "EXISTS ("
            "SELECT 1 "
            "FROM UNNEST(o.opening_hours_specification) AS t(day) "
            "WHERE "
            "day.dayOfWeek = '" + str(day_of_week) + "' "
            "AND CAST(day.opens AS TIME) <= TIME '23:59:00' "
            "AND CAST(day.closes AS TIME) >= TIME '00:00:00'"
            ")"
        )

    return None
