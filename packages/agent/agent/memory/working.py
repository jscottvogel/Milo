
from langchain_core.messages import BaseMessage


class WorkingMemory:
    """
    Working memory is the per-turn message buffer, bounded to prevent context window overflow.
    Older turns are automatically summarized into the thread memory.
    """
    def __init__(self, max_tokens: int = 80000):
        self.max_tokens = max_tokens

    def trim(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        # Basic implementation: just return the last 20 messages for PoC
        # In full implementation, we'd count tokens
        return messages[-20:] if len(messages) > 20 else messages
