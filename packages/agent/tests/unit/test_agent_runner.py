from unittest.mock import MagicMock, patch

import pytest
from agent.runner import AgentRunner


@pytest.mark.asyncio
async def test_agent_runner():
    session = MagicMock()

    with patch('agent.runner.BedrockClient') as mock_bedrock, \
         patch('agent.runner.ThreadMemory') as mock_thread_mem, \
         patch('agent.runner.ProgramMemory') as mock_prog_mem:

        mock_thread_mem.return_value.load_recent_messages.return_value = []
        mock_prog_mem.return_value.get_context.return_value = "Program Context"

        async def mock_stream(*args, **kwargs):
            yield {"type": "token", "content": "hello"}
            yield {"type": "message_stop", "stopReason": "end_turn"}

        mock_bedrock.return_value.invoke_with_streaming = mock_stream

        runner = AgentRunner(session, "tenant1", "thread1", "milo1")

        events = []
        async for event in runner.run_turn("hello"):
            events.append(event)

        assert len(events) == 2
        assert events[0]["type"] == "token"
        assert events[1]["type"] == "done"
