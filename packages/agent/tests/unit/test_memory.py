from unittest.mock import MagicMock

from agent.memory.program import ProgramMemory
from agent.memory.thread import ThreadMemory


def test_thread_memory():
    session = MagicMock()
    tm = ThreadMemory(session, "thread1", "tenant1")

    mock_thread = MagicMock()
    mock_thread.summary = "Test Summary"
    session.query.return_value.filter.return_value.first.return_value = mock_thread

    assert tm.load_summary() == "Test Summary"

    mock_msg_user = MagicMock()
    mock_msg_user.role = "user"
    mock_msg_user.content_jsonb = {"text": "Hello"}

    mock_msg_asst = MagicMock()
    mock_msg_asst.role = "assistant"
    mock_msg_asst.content_jsonb = {"text": "Hi"}

    session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_msg_user, mock_msg_asst]

    messages = tm.load_recent_messages()
    assert len(messages) == 2
    assert messages[0].content == "Hi"
    assert messages[1].content == "Hello"

    tm.save_message("user", "test")
    session.add.assert_called()
    session.commit.assert_called()

def test_program_memory():
    session = MagicMock()
    pm = ProgramMemory(session)

    assert pm.get_context() == "No specific program selected."

    session.query.return_value.filter.return_value.first.return_value = None
    assert pm.get_context("prog1") == "Program not found."

    mock_prog = MagicMock()
    mock_prog.name = "Prog 1"
    mock_prog.description = "Desc"
    mock_prog.status = "active"

    session.query.return_value.filter.return_value.first.return_value = mock_prog
    res = pm.get_context("prog1")
    assert "Prog 1" in res
    assert "Desc" in res
