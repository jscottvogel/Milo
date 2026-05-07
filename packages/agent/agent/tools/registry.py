from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    mutates: bool
    requires_approval: bool

    async def invoke(self, input_data: dict[str, Any], context: Any) -> Any:
        ...

class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)

# Global registry instance
registry = ToolRegistry()
