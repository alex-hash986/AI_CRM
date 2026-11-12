from typing import Literal

from pydantic import BaseModel, Field, JsonValue

from app.schemas.common import EntityId


class DealScoringOutput(BaseModel):
    score: int = Field(ge=0, le=100)
    win_probability: float = Field(ge=0, le=1)
    risk_assessment: str
    next_step: str


class EmailGenerateRequest(BaseModel):
    deal_id: EntityId
    template_type: Literal["follow_up", "cold_outreach", "proposal_pitch", "reengagement"]
    tone: Literal["formal", "friendly", "direct"] = "friendly"
    custom_instructions: str | None = Field(default=None, max_length=4000)


class EmailGenerateOutput(BaseModel):
    subject: str
    body: str
    key_points: list[str]


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, JsonValue] | None = None
