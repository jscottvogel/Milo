import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from agent.tools.context import AgentContext
from agent.tools.registry import Tool


class DeveloperHandoffInput(BaseModel):
    title: str = Field(description="A short, descriptive title for the feature or capability requested")
    description: str = Field(description="A detailed explanation of the requirement and why it is needed")
    acceptance_criteria: list[str] = Field(description="A list of measurable conditions that must be met for this to be considered done")
    technical_notes: str = Field(default="", description="Any technical suggestions, constraints, or context for the software engineer")


class DeveloperHandoffOutput(BaseModel):
    file_path: str = Field(description="The absolute path to the generated requirements markdown file")


class DeveloperHandoffTool(Tool):
    name = "developer.handoff"
    description = "Write a highly structured technical requirements document directly to the engineering team's local workspace so they can build the requested capability."
    input_schema = DeveloperHandoffInput
    output_schema = DeveloperHandoffOutput
    mutates = False
    requires_approval = False

    async def invoke(self, input_data: dict[str, Any], context: AgentContext) -> Any:
        title = input_data["title"]
        
        # Slugify the title
        slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{slug}_{timestamp}.md"
        
        # Resolve the root workspace directory (Milo root)
        # agent/agent/tools/developer.py is 5 levels deep
        root_dir = Path(__file__).parent.parent.parent.parent.parent
        docs_dir = root_dir / "docs" / "requests"
        
        # Ensure the directory exists
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = docs_dir / filename
        
        # Format the markdown content
        content = f"# {title}\n\n"
        content += f"**Date:** {datetime.now().isoformat()}\n"
        content += f"**Tenant ID:** {context.tenant_id}\n\n"
        
        content += f"## Description\n{input_data['description']}\n\n"
        
        content += "## Acceptance Criteria\n"
        for ac in input_data['acceptance_criteria']:
            content += f"- [ ] {ac}\n"
        content += "\n"
        
        if input_data.get('technical_notes'):
            content += f"## Technical Notes\n{input_data['technical_notes']}\n"
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return DeveloperHandoffOutput(file_path=str(file_path)).model_dump()
