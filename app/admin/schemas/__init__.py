from pydantic import BaseModel


class AdminSetUserStatusIn(BaseModel):
    status: str
    reason: str | None = None

