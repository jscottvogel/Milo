import os
import subprocess
import tempfile
from typing import Any

from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool

class DocumentGenerateInput(BaseModel):
    markdown_content: str = Field(description="The full Markdown content to compile into the document.")
    output_format: str = Field(description="The desired format of the document. Must be 'pdf', 'docx', or 'pptx'.")
    output_filename: str = Field(description="The name of the file to generate (e.g. 'proposal.pdf'). Must include the correct extension.")

class DocumentGenerateOutput(BaseModel):
    file_path: str
    status: str

class DocumentGenerateTool(Tool):
    name = "document__generate"
    description = "Compile Markdown content into a rich formatted PDF, Word Document (DOCX), or PowerPoint (PPTX) file."
    input_schema = DocumentGenerateInput
    output_schema = DocumentGenerateOutput
    mutates = True
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        content = input_data["markdown_content"]
        fmt = input_data["output_format"].lower().strip()
        filename = input_data["output_filename"]
        
        if fmt not in ["pdf", "docx", "pptx"]:
            return {"error": "output_format must be 'pdf', 'docx', or 'pptx'."}
            
        # Ensure we write the output file to the workspace root
        workspace_root = os.getcwd()
        output_path = os.path.join(workspace_root, filename)
        
        try:
            if fmt == "pdf":
                # Use md-to-pdf via Node.js
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_md:
                    temp_md.write(content)
                    temp_md_path = temp_md.name
                    
                try:
                    # Run npx md-to-pdf. On Windows shell=True is needed for npx to resolve correctly.
                    subprocess.run(
                        ["npx", "--yes", "md-to-pdf", temp_md_path, "--basedir", workspace_root],
                        check=True,
                        capture_output=True,
                        shell=True
                    )
                    
                    # md-to-pdf outputs a file with .pdf extension next to the original
                    generated_pdf = temp_md_path.replace(".md", ".pdf")
                    if os.path.exists(generated_pdf):
                        import shutil
                        shutil.move(generated_pdf, output_path)
                    else:
                        raise Exception("md-to-pdf failed to generate the expected PDF file.")
                finally:
                    # Cleanup
                    if os.path.exists(temp_md_path):
                        os.remove(temp_md_path)
                        
            elif fmt in ["docx", "pptx"]:
                # Use pypandoc
                import pypandoc
                
                # Ensure pandoc is downloaded if not present
                try:
                    pypandoc.get_pandoc_version()
                except OSError:
                    pypandoc.download_pandoc()
                    
                pypandoc.convert_text(content, fmt, format='md', outputfile=output_path)
                
            return DocumentGenerateOutput(
                file_path=output_path,
                status="success"
            ).model_dump()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to generate {fmt} document: {str(e)}")
            return {"error": f"Failed to generate document: {str(e)}"}
