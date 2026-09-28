from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from booking_api.database import get_db, init_db
from booking_api.models import Booking, BookingCreate

if TYPE_CHECKING:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="カウンセリング予約APIスタブ",
    description="カウンセリング予約情報を受け取り、SQLiteに保存するAPI",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post(
    "/bookings",
    response_model=Booking,
    status_code=status.HTTP_201_CREATED,
    summary="予約登録",
    description="カウンセリング予約情報を登録する",
)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
) -> Booking:
    booking = Booking(
        name=booking_data.name,
        email=booking_data.email,
        booking_datetime=booking_data.booking_datetime,
        consultation_content=booking_data.consultation_content,
        counseling_office_name=booking_data.counseling_office_name,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/health", summary="ヘルスチェック")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
