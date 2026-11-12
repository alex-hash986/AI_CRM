from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.communication import CommunicationLog
    from app.models.pipeline import PipelineStage


class Deal(TimestampMixin, Base):
    __tablename__ = "deals"
    __table_args__ = (
        CheckConstraint("ai_score BETWEEN 0 AND 100", name="ck_deals_ai_score"),
        CheckConstraint(
            "ai_win_probability BETWEEN 0 AND 1", name="ck_deals_ai_win_probability"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    budget: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    stage_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_stages.id", ondelete="RESTRICT"), index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), index=True
    )
    ai_score: Mapped[int | None]
    ai_win_probability: Mapped[float | None] = mapped_column(Float)
    ai_next_step: Mapped[str | None] = mapped_column(Text)
    ai_risk_assessment: Mapped[str | None] = mapped_column(Text)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    stage: Mapped[PipelineStage] = relationship(back_populates="deals")
    client: Mapped[Client] = relationship(back_populates="deals")
    communications: Mapped[list[CommunicationLog]] = relationship(
        back_populates="deal", passive_deletes="all"
    )
