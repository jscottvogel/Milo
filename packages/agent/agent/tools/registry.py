import importlib
import inspect
import logging
import pkgutil
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from .context import AgentContext


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel] | None
    mutates: bool
    requires_approval: bool

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        ...


logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self._discovered = False

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        self.discover_tools()
        return self.tools.get(name)

    def get_all_tools(self) -> list[Tool]:
        self.discover_tools()
        return list(self.tools.values())

    def discover_tools(self):
        if self._discovered:
            return
        
        # Avoid circular imports by importing here
        import agent.tools

        for _, module_name, is_pkg in pkgutil.iter_modules(agent.tools.__path__):
            if is_pkg or module_name in ('registry', 'wrapper', 'context'):
                continue
            
            full_module_name = f"agent.tools.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and not inspect.isabstract(obj):
                        # Instantiate the tool to register it if it implements the Protocol
                        # We assume tools have a zero-argument constructor
                        if hasattr(obj, 'name') and hasattr(obj, 'invoke') and obj.__name__ != "Tool":
                            try:
                                instance = obj()
                                if isinstance(instance, Tool):
                                    self.register(instance)
                                    logger.debug(f"Registered tool: {instance.name}")
                            except Exception as e:
                                logger.warning(f"Failed to instantiate tool {name}: {e}")
            except Exception as e:
                logger.error(f"Failed to load tools from {full_module_name}: {e}")
                
        self._discovered = True


# Global registry instance
registry = ToolRegistry()
