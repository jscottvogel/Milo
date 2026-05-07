from typing import Any

from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class WebSearchInput(BaseModel):
    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum number of results to return")


class WebSearchOutput(BaseModel):
    results: list[dict[str, str]]


class WebSearchTool(Tool):
    name = "web.search"
    description = "Search the web for current information. Use this when you need facts or data not in memory."
    input_schema = WebSearchInput
    output_schema = WebSearchOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        try:
            from duckduckgo_search import DDGS
            
            ddgs = DDGS()
            # ddgs.text is synchronous, run in executor
            import asyncio
            loop = asyncio.get_running_loop()
            
            # Using list to force generator evaluation
            results = await loop.run_in_executor(
                None, 
                lambda: list(ddgs.text(input_data["query"], max_results=input_data.get("max_results", 5)))
            )
            
            return WebSearchOutput(results=results).model_dump()
        except ImportError:
            return {"error": "duckduckgo_search library not installed"}
        except Exception as e:
            return {"error": str(e)}


class WebFetchInput(BaseModel):
    url: str = Field(description="The URL to fetch")


class WebFetchOutput(BaseModel):
    text: str = Field(description="The extracted text from the page")


class WebFetchTool(Tool):
    name = "web.fetch"
    description = "Fetch and extract text content from a web page URL."
    input_schema = WebFetchInput
    output_schema = WebFetchOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.get(input_data["url"])
                response.raise_for_status()
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # Truncate text if it's too long (e.g., 10000 characters)
            max_chars = 10000
            if len(text) > max_chars:
                text = text[:max_chars] + "... [truncated]"
                
            return WebFetchOutput(text=text).model_dump()
        except ImportError:
            return {"error": "httpx or beautifulsoup4 library not installed"}
        except Exception as e:
            return {"error": str(e)}
