from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.deal import Deal


class CommunicationLog(TimestampMixin, Base):
    __tablename__ = "communication_logs"
    __table_args__ = (
        UniqueConstraint("telegram_update_id", name="uq_communication_logs_telegram_update_id"),
        CheckConstraint(
            "channel IN ('email', 'telegram', 'call', 'note')",
            name="ck_communication_logs_channel",
        ),
        CheckConstraint(
            "direction IN ('inbound', 'outbound')", name="ck_communication_logs_direction"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int | None] = mapped_column(
        ForeignKey("deals.id", ondelete="SET NULL"), index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="RESTRICT"), index=True
    )
    telegram_update_id: Mapped[int | None] = mapped_column(BigInteger)
    channel: Mapped[str] = mapped_column(String(16))
    direction: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    ai_summary: Mapped[str | None] = mapped_column(Text)

    deal: Mapped[Deal | None] = relationship(back_populates="communications")
    client: Mapped[Client] = relationship(back_populates="communications")
