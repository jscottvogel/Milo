
from sqlalchemy.orm import Session


class SemanticMemory:
    """
    Key-value fact store lookup against memory_facts.
    """
    def __init__(self, session: Session):
        self.session = session

    def get_fact(self, key: str) -> str | None:
        # Phase 3 placeholder
        return None
