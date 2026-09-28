from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from pydantic import EmailStr
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    pass


def utc_now() -> datetime:
    return datetime.now(UTC)


class BookingBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    booking_datetime: datetime
    consultation_content: str = Field(min_length=1)
    counseling_office_name: str = Field(min_length=1, max_length=200)


class Booking(BookingBase, table=True):
    __tablename__: str = "bookings"  # pyright: ignore[reportIncompatibleVariableOverride]

    id: int | None = Field(default=None, primary_key=True)
    booking_datetime: datetime = Field(sa_type=sa.DateTime(timezone=False), nullable=False)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    model_config = {"from_attributes": True}


class BookingCreate(BookingBase):
    pass
