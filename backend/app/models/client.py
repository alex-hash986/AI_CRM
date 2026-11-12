from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.communication import CommunicationLog
    from app.models.deal import Deal


class Client(TimestampMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("telegram_chat_id", name="uq_clients_telegram_chat_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(64))
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32), server_default="active")
    custom_fields: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB), default=dict, server_default=text("'{}'::jsonb")
    )

    deals: Mapped[list[Deal]] = relationship(back_populates="client", passive_deletes="all")
    communications: Mapped[list[CommunicationLog]] = relationship(
        back_populates="client", passive_deletes="all"
    )
