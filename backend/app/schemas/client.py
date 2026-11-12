from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, EmailStr, Field, JsonValue, StringConstraints, model_validator

from app.schemas.common import EntityResponse, Name
from app.schemas.deal import DealShortResponse


def validate_phone(value: str) -> str:
    if not 7 <= sum(char.isdigit() for char in value) <= 15:
        raise ValueError("Phone must contain 7 to 15 digits")
    return value


Phone = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, pattern=r"^\+?[0-9() .-]*[0-9][0-9() .-]*$", max_length=64
    ),
    AfterValidator(validate_phone),
]
ClientStatus = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]


class ClientCreate(BaseModel):
    name: Name
    company: Name | None = None
    email: Annotated[EmailStr, Field(max_length=320)] | None = None
    phone: Phone | None = None
    status: ClientStatus = "active"
    custom_fields: dict[str, JsonValue] = Field(default_factory=dict)


class ClientUpdate(BaseModel):
    name: Name | None = None
    company: Name | None = None
    email: Annotated[EmailStr, Field(max_length=320)] | None = None
    phone: Phone | None = None
    status: ClientStatus | None = None
    custom_fields: dict[str, JsonValue] | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> Self:
        for field in ("name", "status", "custom_fields"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ClientResponse(EntityResponse):
    name: str
    company: str | None
    email: str | None
    phone: str | None
    status: str
    custom_fields: dict[str, JsonValue]


class ClientDetailResponse(ClientResponse):
    deals: list[DealShortResponse]
