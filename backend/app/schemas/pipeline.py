from app.schemas.common import ORMResponse
from app.schemas.deal import DealShortResponse


class PipelineStageResponse(ORMResponse):
    id: int
    name: str
    order: int
    color: str
    is_won: bool
    is_lost: bool


class BoardStageResponse(PipelineStageResponse):
    deals: list[DealShortResponse]


class BoardResponse(ORMResponse):
    pipeline_id: int
    stages: list[BoardStageResponse]
