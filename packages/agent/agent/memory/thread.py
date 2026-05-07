from db.models import Message, Thread
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.orm import Session


class ThreadMemory:
    """
    Thread memory handles loading and saving the rolling summary and recent messages from the database.
    """
    def __init__(self, session: Session, thread_id: str, tenant_id: str):
        self.session = session
        self.thread_id = thread_id
        self.tenant_id = tenant_id

    def load_summary(self) -> str:
        thread = self.session.query(Thread).filter(Thread.id == self.thread_id).first()
        return thread.summary if thread and thread.summary else ""

    def load_recent_messages(self, limit: int = 20) -> list[BaseMessage]:
        db_messages = self.session.query(Message).filter(
            Message.thread_id == self.thread_id
        ).order_by(Message.created_at.desc()).limit(limit).all()

        result = []
        for msg in reversed(db_messages):
            if msg.role == "user":
                result.append(HumanMessage(content=msg.content_jsonb.get("text", "")))
            elif msg.role == "assistant":
                result.append(AIMessage(content=msg.content_jsonb.get("text", "")))
        return result

    def save_message(self, role: str, content: str) -> None:
        msg = Message(thread_id=self.thread_id, tenant_id=self.tenant_id, role=role, content_jsonb={"text": content})
        self.session.add(msg)
        self.session.commit()
