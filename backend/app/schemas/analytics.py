from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, StringConstraints

CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class StageMetrics(BaseModel):
    stage_id: int
    stage_name: str
    deal_count: int
    total_amount: Decimal
    weighted_amount: Decimal


class SalesDashboardResponse(BaseModel):
    currency: str | None
    total_pipeline_value: Decimal
    weighted_forecast_value: Decimal
    won_deals_revenue: Decimal
    average_ai_score: float | None
    conversion_rate: float
    stages_breakdown: list[StageMetrics]
