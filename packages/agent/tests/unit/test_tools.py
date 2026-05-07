import pytest

from agent.tools.registry import registry
from agent.tools.memory import MemorySearchTool, MemoryWriteTool
from agent.tools.program import ProgramReadTool, ProgramUpdateTool
from agent.tools.email import EmailDraftTool
from agent.tools.calendar import CalendarReadTool
from agent.tools.storage import StorageReadTool, StorageWriteTool
from agent.tools.web import WebSearchTool, WebFetchTool
from agent.tools.handoff import HandoffHumanTool


def test_tool_registry_discovery():
    # Calling get_all_tools should trigger discovery
    tools = registry.get_all_tools()
    
    # We should have at least 11 tools registered
    assert len(tools) >= 11
    
    tool_names = [t.name for t in tools]
    assert "memory.search" in tool_names
    assert "memory.write" in tool_names
    assert "program.read" in tool_names
    assert "program.update" in tool_names
    assert "email.draft" in tool_names
    assert "calendar.read" in tool_names
    assert "storage.read" in tool_names
    assert "storage.write" in tool_names
    assert "web.search" in tool_names
    assert "web.fetch" in tool_names
    assert "handoff.human" in tool_names


def test_tool_schemas():
    # Verify that all registered tools have valid Pydantic schemas
    for t in registry.get_all_tools():
        assert hasattr(t, "input_schema")
        assert t.input_schema is not None
        
        # Check required fields
        assert isinstance(t.mutates, bool)
        assert isinstance(t.requires_approval, bool)
