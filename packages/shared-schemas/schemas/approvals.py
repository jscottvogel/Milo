import datetime
from typing import Any

from pydantic import BaseModel


class ApprovalResponse(BaseModel):
    id: str
    milo_id: str
    thread_id: str
    tool_name: str
    payload: dict[str, Any]
    status: str
    expires_at: datetime.datetime
    decided_by: str | None = None
    decided_at: datetime.datetime | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: str
    modified_payload: dict[str, Any] | None = None
