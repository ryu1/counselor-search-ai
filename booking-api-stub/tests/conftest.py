from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel

from booking_api.database import get_db
from booking_api.main import app
from booking_api.models import Booking

if TYPE_CHECKING:
    pass


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        SQLModel.metadata.create_all(bind=engine)

        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def valid_booking_data() -> dict:
    return {
        "name": "田中太郎",
        "email": "tanaka@example.com",
        "booking_datetime": "2026-10-01T10:00:00",
        "consultation_content": "仕事のストレスについて相談したい",
        "counseling_office_name": "東京カウンセリングオフィス",
    }