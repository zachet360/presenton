from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import JSON, Column, DateTime, String, Integer
from sqlmodel import Field, SQLModel

from utils.datetime_utils import get_current_utc_datetime


class GenerationLogModel(SQLModel, table=True):
    __tablename__ = "generation_logs"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    presentation_id: Optional[uuid.UUID] = None
    filename: str = Field(sa_column=Column(String, index=True))
    status: str = Field(default="running", sa_column=Column(String, default="running"))
    started_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, default=get_current_utc_datetime
        ),
    )
    finished_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )
    total_duration_ms: Optional[int] = Field(
        sa_column=Column(Integer, nullable=True), default=None
    )
    steps: list = Field(sa_column=Column(JSON), default=[])
    error: Optional[str] = Field(sa_column=Column(String, nullable=True), default=None)
