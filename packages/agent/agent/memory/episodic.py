
from sqlalchemy.orm import Session


class EpisodicMemory:
    """
    Top-k vector search against memory_chunks using pgvector.
    Embedding generation uses Amazon Titan Text Embeddings v2.
    """
    def __init__(self, session: Session):
        self.session = session

    def search(self, query: str, k: int = 5) -> list[str]:
        # Phase 3 placeholder: Vector search implemented in Phase 4/5
        return []
