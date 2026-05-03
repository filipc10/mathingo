from uuid import UUID

from pydantic import BaseModel, Field


class SubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class SubscribeRequest(BaseModel):
    endpoint: str
    keys: SubscriptionKeys
    device_label: str | None = Field(default=None, max_length=100)
    user_agent: str | None = None


class SubscribeResponse(BaseModel):
    subscription_id: UUID
    status: str = "ok"


class UnsubscribeResponse(BaseModel):
    status: str = "ok"


class TestPushResponse(BaseModel):
    sent: int
    total: int


class VapidPublicKeyResponse(BaseModel):
    key: str
