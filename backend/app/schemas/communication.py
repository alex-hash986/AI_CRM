from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.schemas.common import EntityId, EntityResponse

Channel = Literal["email", "telegram", "call", "note"]
Direction = Literal["inbound", "outbound"]


class CommunicationLogCreate(BaseModel):
    deal_id: EntityId | None = None
    client_id: EntityId
    channel: Channel
    direction: Direction
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CommunicationLogResponse(EntityResponse):
    deal_id: int | None
    client_id: int
    channel: Channel
    direction: Direction
    content: str
    ai_summary: str | None


class CommunicationCreateResponse(CommunicationLogResponse):
    task_id: str | None = None
