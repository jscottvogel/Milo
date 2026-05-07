from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.llm.bedrock import BedrockClient, LLMUsage


def test_llm_usage():
    usage = LLMUsage("anthropic.claude-3-5-sonnet-20241022-v2:0", 1000, 1000)
    # sonnet: 0.003 + 0.015 = 0.018
    assert usage.cost_usd == 0.018

@pytest.mark.asyncio
async def test_bedrock_invoke():
    client = BedrockClient()

    # Mock boto3 run_in_executor
    mock_response = {
        'stream': [
            {'contentBlockDelta': {'delta': {'text': 'Hello'}}},
            {'metadata': {'usage': {'inputTokens': 10, 'outputTokens': 10}}},
            {'messageStop': {'stopReason': 'end_turn'}}
        ]
    }

    with patch("asyncio.get_running_loop") as mock_loop:
        loop_mock = MagicMock()
        mock_loop.return_value = loop_mock
        loop_mock.run_in_executor = AsyncMock(return_value=mock_response)

        events = []
        async for event in client.invoke_with_streaming([], "sys", []):
            events.append(event)

        assert len(events) == 3
        assert events[0]["type"] == "token"
        assert events[0]["content"] == "Hello"
        assert events[1]["type"] == "usage"
        assert events[2]["type"] == "message_stop"
