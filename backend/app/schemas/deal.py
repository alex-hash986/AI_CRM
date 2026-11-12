from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.schemas.common import EntityId, EntityResponse, Name, ORMResponse

Budget = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=2)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class DealCreate(BaseModel):
    title: Name
    budget: Budget
    currency: Currency
    stage_id: EntityId
    client_id: EntityId


class DealUpdate(BaseModel):
    title: Name | None = None
    budget: Budget | None = None
    currency: Currency | None = None
    client_id: EntityId | None = None

    @model_validator(mode="after")
    def reject_null_fields(self) -> Self:
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class DealStageUpdate(BaseModel):
    stage_id: EntityId


class DealShortResponse(ORMResponse):
    id: int
    title: str
    budget: Decimal
    currency: str
    client_id: int
    stage_id: int
    ai_score: int | None
    ai_win_probability: float | None


class DealResponse(DealShortResponse, EntityResponse):
    ai_next_step: str | None
    ai_risk_assessment: str | None
    closed_at: datetime | None
