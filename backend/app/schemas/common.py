from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

T = TypeVar("T")
EntityId = Annotated[int, Field(gt=0)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EntityResponse(ORMResponse):
    id: int
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
