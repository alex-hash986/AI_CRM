from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.deal import Deal


class Pipeline(TimestampMixin, Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    stages: Mapped[list[PipelineStage]] = relationship(
        back_populates="pipeline", cascade="all, delete-orphan",
        passive_deletes=True, order_by="PipelineStage.order",
    )


class PipelineStage(TimestampMixin, Base):
    __tablename__ = "pipeline_stages"
    __table_args__ = (
        UniqueConstraint("pipeline_id", "order", name="uq_pipeline_stages_pipeline_order"),
        CheckConstraint('"order" >= 0', name="ck_pipeline_stages_order"),
        CheckConstraint("NOT (is_won AND is_lost)", name="ck_pipeline_stages_outcome"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    order: Mapped[int]
    color: Mapped[str] = mapped_column(String(32))
    is_won: Mapped[bool] = mapped_column(server_default=false())
    is_lost: Mapped[bool] = mapped_column(server_default=false())

    pipeline: Mapped[Pipeline] = relationship(back_populates="stages")
    deals: Mapped[list[Deal]] = relationship(back_populates="stage", passive_deletes="all")
