from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from booking_api.models import Booking

if TYPE_CHECKING:
    pass


class TestCreateBooking:
    def test_create_booking_success(self, client: TestClient, test_db: Session, valid_booking_data: dict) -> None:
        response = client.post("/bookings", json=valid_booking_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == valid_booking_data["name"]
        assert data["email"] == valid_booking_data["email"]
        assert data["consultation_content"] == valid_booking_data["consultation_content"]
        assert data["counseling_office_name"] == valid_booking_data["counseling_office_name"]
        assert "id" in data
        assert "created_at" in data

        booking = test_db.query(Booking).filter(Booking.id == data["id"]).first()
        assert booking is not None
        assert booking.name == valid_booking_data["name"]
        assert booking.email == valid_booking_data["email"]
        assert booking.booking_datetime == datetime.fromisoformat(valid_booking_data["booking_datetime"])
        assert booking.consultation_content == valid_booking_data["consultation_content"]
        assert booking.counseling_office_name == valid_booking_data["counseling_office_name"]

    def test_create_booking_missing_name(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        del data["name"]
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_missing_email(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        del data["email"]
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_missing_booking_datetime(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        del data["booking_datetime"]
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_missing_consultation_content(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        del data["consultation_content"]
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_missing_counseling_office_name(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        del data["counseling_office_name"]
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_invalid_email(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        data["email"] = "invalid-email"
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_invalid_datetime(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        data["booking_datetime"] = "invalid-datetime"
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_empty_name(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        data["name"] = ""
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_empty_consultation_content(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        data["consultation_content"] = ""
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_empty_counseling_office_name(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        data["counseling_office_name"] = ""
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_name_too_long(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        data["name"] = "a" * 101
        response = client.post("/bookings", json=data)
        assert response.status_code == 422

    def test_create_booking_counseling_office_name_too_long(self, client: TestClient, valid_booking_data: dict) -> None:
        data = valid_booking_data.copy()
        data["counseling_office_name"] = "a" * 201
        response = client.post("/bookings", json=data)
        assert response.status_code == 422


class TestHealthCheck:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}