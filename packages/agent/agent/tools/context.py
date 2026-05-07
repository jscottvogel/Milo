from dataclasses import dataclass
from typing import Any
from sqlalchemy.orm import Session

@dataclass
class AgentContext:
    session: Session
    tenant_id: str
    milo_id: str
    thread_id: str
    integration_tokens: dict[str, str] = field(default_factory=dict)
