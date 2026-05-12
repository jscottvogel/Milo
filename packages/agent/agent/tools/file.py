import os
from typing import Any

from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool
from agent.tools.temp_manager import TempFileManager
from agent.tools.metadata import extract_metadata, format_metadata_header

class FileReadInput(BaseModel):
    file_path: str = Field(description="The absolute or relative path to the file, or a tenant storage path (e.g. uploads/...).")

class FileReadOutput(BaseModel):
    content: str
    metadata: dict[str, Any]

class FileReadTool(Tool):
    name = "file__read"
    description = "Read and parse the contents of a local file or storage path (supports PDF, DOCX, XLSX, PPTX, HTML, TXT, etc.) into Markdown."
    input_schema = FileReadInput
    output_schema = FileReadOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        original_path = input_data["file_path"]
        file_path = original_path
        is_temp_s3 = False
        
        SUPPORTED_EXTS = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.md', '.html', '.csv', '.json', '.yaml']
        ext = os.path.splitext(file_path)[1].lower()
        if ext and ext not in SUPPORTED_EXTS:
            return {"error": f"Format {ext} is not supported. Supported: {', '.join(SUPPORTED_EXTS)}"}

        # Detection rules:
        # 1. Start with uploads/ -> STORAGE
        # 2. Start with / or ./ or ../ -> LOCAL
        # 3. Exists -> LOCAL
        # 4. Fallback -> STORAGE

        is_storage = False
        if file_path.startswith("uploads/"):
            is_storage = True
        elif file_path.startswith("/") or file_path.startswith("./") or file_path.startswith("../"):
            is_storage = False
        elif os.path.exists(file_path):
            is_storage = False
        else:
            is_storage = True

        if is_storage:
            import boto3
            import asyncio
            
            bucket = os.environ.get("S3_BUCKET_NAME", "milo-poc-bucket-jsco")
            key = f"{context.tenant_id}/{file_path}"
            
            try:
                temp_path = TempFileManager.get_temp_path(file_path)
            except Exception as e:
                return {"error": f"Could not create temp file for parsing: {e}"}
                
            try:
                s3 = boto3.client("s3")
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: s3.download_file(bucket, key, temp_path))
                file_path = temp_path
                is_temp_s3 = True
            except Exception as e:
                # If fallback detection failed, it might have been meant to be local but just wasn't found
                if not original_path.startswith("uploads/"):
                    return {"error": f"File not found at local or storage path: {original_path}"}
                return {"error": f"File not found at storage path: {original_path}"}
        else:
            # Ensure the file exists locally
            if not os.path.exists(file_path):
                workspace_root = os.getcwd()
                resolved_path = os.path.join(workspace_root, file_path)
                if not os.path.exists(resolved_path):
                    return {"error": f"File not found: {original_path}"}
                file_path = resolved_path
            
        try:
            from markitdown import MarkItDown
            
            # Extract metadata
            metadata = extract_metadata(file_path, original_filename=original_path)
            
            md = MarkItDown()
            try:
                result = md.convert(file_path)
                content = result.text_content
                if not content:
                    content = "(No text content extracted from this file)"
            except Exception as parse_err:
                return {"error": f"Parse incomplete: {parse_err}"}
            
            # Approximate word count
            word_count = len(content.split())
            metadata["words"] = str(word_count)
            
            # Prepend metadata header
            header = format_metadata_header(metadata)
            final_content = header + content
                
            return FileReadOutput(
                content=final_content,
                metadata=metadata
            ).model_dump()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to parse file {original_path}: {str(e)}")
            return {"error": f"File content appears corrupted or unreadable: {str(e)}"}
        finally:
            if is_temp_s3 and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
