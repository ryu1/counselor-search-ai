"""Data models for the search_counselors Lambda function.

Defines the data structures used for search conditions,
results, and intermediate processing.
"""

from typing import Any, Dict, List, Optional


class SearchConditions:
    """Search conditions parsed from the Tool input.

    Attributes:
        stations: List of nearest station master values
        area_of_expertise: List of expertise master values
        methods: List of counseling method master values
        genders: List of gender master values
        ages: List of age master values
        requested_datetime: Dict with datetime condition details
    """

    def __init__(
        self,
        stations: List[str],
        area_of_expertise: List[str],
        methods: List[str],
        genders: List[str],
        ages: List[str],
        requested_datetime: Optional[dict[str, Any]],
    ):
        self.stations = stations or []
        self.area_of_expertise = area_of_expertise or []
        self.methods = methods or []
        self.genders = genders or []
        self.ages = ages or []
        self.requested_datetime = requested_datetime


class SearchResult:
    """The result of a counselor search operation."""

    def __init__(
        self,
        count: int,
        results: List[dict[str, Any]],
    ):
        self.count = count
        self.results = results


class OfficeSearchResult:
    """Office-level search result with matched counselors."""

    def __init__(
        self,
        office_id: str,
        office_name: str,
        nearest_stations: List[str],
        matched_counselors: List[dict[str, Any]],
    ):
        self.office_id = office_id
        self.office_name = office_name
        self.nearest_stations = nearest_stations or []
        self.matched_counselors = matched_counselors or []


class DateTimeCondition:
    """Date/time search condition structure."""

    def __init__(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        day_of_week: Optional[str] = None,
        around: Optional[str] = None,
        tolerance_minutes: int = 60,
    ):
        self.start = start
        self.end = end
        self.day_of_week = day_of_week
        self.around = around
        self.tolerance_minutes = tolerance_minutes