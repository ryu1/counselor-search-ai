from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

from sqlalchemy.orm import Session as SQLAlchemySession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./tmp/booking.db")
    return database_url


def ensure_database_directory(database_url: str) -> None:
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)


engine = None


def get_engine():
    global engine
    if engine is None:
        database_url = get_database_url()
        ensure_database_directory(database_url)
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
            echo=False,
        )
        SQLModel.metadata.create_all(bind=engine)
    return engine


SessionLocal = None


def get_session_local():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal


def get_db() -> Generator[SQLAlchemySession, Any, Any]:
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    get_engine()
