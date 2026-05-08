import os
from typing import Any

from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

class FileReadInput(BaseModel):
    file_path: str = Field(description="The absolute or relative path to the file (e.g. document.pdf, data.xlsx, report.docx).")

class FileReadOutput(BaseModel):
    content: str
    metadata: dict[str, Any]

class FileReadTool(Tool):
    name = "file.read"
    description = "Read and parse the contents of a local file (supports PDF, DOCX, XLSX, PPTX, HTML, TXT, etc.) into Markdown."
    input_schema = FileReadInput
    output_schema = FileReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        file_path = input_data["file_path"]
        
        # Ensure the file exists
        if not os.path.exists(file_path):
            # Try to resolve relative to workspace root (assuming running from Milo directory)
            workspace_root = os.getcwd()
            resolved_path = os.path.join(workspace_root, file_path)
            if not os.path.exists(resolved_path):
                return {"error": f"File not found: {file_path}"}
            file_path = resolved_path
            
        try:
            from markitdown import MarkItDown
            
            md = MarkItDown()
            result = md.convert(file_path)
            
            # Text content can be extremely long. Bedrock context window is huge (200k+), 
            # but we might want to ensure we return it efficiently.
            content = result.text_content
            if not content:
                content = "(No text content extracted from this file)"
                
            return FileReadOutput(
                content=content,
                metadata={} # Future: could add page count, word count, etc if markitdown supports it
            ).model_dump()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to parse file {file_path}: {str(e)}")
            return {"error": f"Failed to parse file: {str(e)}"}
