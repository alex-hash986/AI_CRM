from typing import Annotated, Literal, Self

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator, model_validator

from app.schemas.common import EntityId
from app.schemas.communication import CommunicationLogResponse

MessageText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100000)]
ChatId = Annotated[int, Field(gt=0, le=2**52 - 1)]
UpdateId = Annotated[int, Field(ge=0, le=2**63 - 1)]


class EmailSendRequest(BaseModel):
    deal_id: EntityId
    to_email: EmailStr
    subject: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    body: MessageText

    @field_validator("subject", mode="before")
    @classmethod
    def validate_header(cls, value: object) -> object:
        if isinstance(value, str) and any(char in value for char in "\r\n\0"):
            raise ValueError("Subject must be a single line")
        return value


class EmailSendResponse(BaseModel):
    status: Literal["sent"] = "sent"
    delivery_mode: Literal["smtp", "demo"]
    communication: CommunicationLogResponse


class TelegramChat(BaseModel):
    id: int
    type: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: str | None = None


class TelegramUpdate(BaseModel):
    update_id: UpdateId | None = None
    message: TelegramMessage | None = None
    chat_id: ChatId | None = None
    username: Annotated[str, Field(max_length=255)] | None = None
    text: MessageText | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> Self:
        if self.update_id is None and (self.chat_id is None or self.text is None):
            raise ValueError("Provide a Telegram update_id or a chat_id with text")
        return self


class TelegramWebhookResponse(BaseModel):
    status: Literal["accepted", "duplicate", "ignored"]
    communication_id: int | None = None
    deal_id: int | None = None
    task_id: str | None = None
