import os

# Layer 1: Identity
# Layer 2: Persona Pack
# Layer 3: Program Context
# Layer 4: Memory Injections
# Layer 5: Tool Catalog

def get_prompt_text(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ""

def build_system_prompt(
    persona_pack: str = "sme",
    program_context: str = "",
    memory_injections: str = ""
) -> str:
    """
    Assembles the 5-layer system prompt for Bedrock execution.
    """
    layers = []

    # Layer 1: Identity
    layers.append("<layer name=\"identity\">")
    layers.append(get_prompt_text("identity.md"))
    layers.append("</layer>")

    # Layer 2: Persona Pack
    layers.append(f"<layer name=\"persona\" pack=\"{persona_pack}\">")
    layers.append(get_prompt_text(f"packs/{persona_pack}.md") or f"You are assisting a {persona_pack} professional.")
    layers.append("</layer>")

    # Layer 3: Program Context
    layers.append("<layer name=\"program_context\">")
    layers.append(program_context if program_context else "No active program context.")
    layers.append("</layer>")

    # Layer 4: Memory Injections
    layers.append("<layer name=\"memory_injections\">")
    layers.append(memory_injections if memory_injections else "No relevant memory retrieved.")
    layers.append("</layer>")

    # Layer 5: Tool Catalog is handled by Bedrock toolConfig, but we can add instructions here
    layers.append("<layer name=\"instructions\">")
    layers.append("Use your tools to accomplish the user's request. Always confirm actions using tools when available.")
    layers.append("</layer>")

    return "\n\n".join(layers)
