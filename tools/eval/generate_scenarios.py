import os

scenarios = {
    "06_memory_search.yaml": """name: "Memory Search"
description: "Agent uses memory.search to find past facts"
messages:
  - role: "user"
    content: "What did we decide about the database migration strategy yesterday?"
expected_tools:
  - "memory.search"
""",
    "07_memory_write.yaml": """name: "Memory Write"
description: "Agent uses memory.write to store a fact"
messages:
  - role: "user"
    content: "Please remember that the staging server IP changed to 192.168.1.100."
expected_tools:
  - "memory.write"
""",
    "08_program_read.yaml": """name: "Program Read"
description: "Agent uses program.read to check active programs"
messages:
  - role: "user"
    content: "Can you list all my active programs?"
expected_tools:
  - "program.read"
""",
    "09_program_update.yaml": """name: "Program Update"
description: "Agent uses program.update to modify a program"
messages:
  - role: "user"
    content: "Update the status of the 'Alpha Release' program to 'executing'."
expected_tools:
  - "program.update"
""",
    "10_email_draft.yaml": """name: "Email Draft"
description: "Agent uses email.draft to prepare an email"
messages:
  - role: "user"
    content: "Draft an email to the team letting them know the build is fixed."
expected_tools:
  - "email.draft"
""",
    "11_calendar_read.yaml": """name: "Calendar Read"
description: "Agent uses calendar.read to check schedule"
messages:
  - role: "user"
    content: "What meetings do I have scheduled for tomorrow?"
expected_tools:
  - "calendar.read"
""",
    "12_storage_read.yaml": """name: "Storage Read"
description: "Agent uses storage.read to access a file"
messages:
  - role: "user"
    content: "Read the contents of the config.json file in my storage."
expected_tools:
  - "storage.read"
""",
    "13_storage_write.yaml": """name: "Storage Write"
description: "Agent uses storage.write to save a file"
messages:
  - role: "user"
    content: "Save the following notes to a file called notes.txt in my storage."
expected_tools:
  - "storage.write"
""",
    "14_web_search.yaml": """name: "Web Search"
description: "Agent uses web.search to find current information"
messages:
  - role: "user"
    content: "What are the latest news about generative AI models?"
expected_tools:
  - "web.search"
""",
    "15_handoff.yaml": """name: "Human Handoff"
description: "Agent uses handoff.human to escalate"
messages:
  - role: "user"
    content: "I'm extremely upset, this is a critical production incident and you can't help me! Get me a human now!"
expected_tools:
  - "handoff.human"
"""
}

base_dir = r"C:\Users\j_sco\projects\Milo\Milo\tools\eval\scenarios"
os.makedirs(base_dir, exist_ok=True)

for filename, content in scenarios.items():
    with open(os.path.join(base_dir, filename), "w") as f:
        f.write(content)

print("Created 10 eval scenarios.")
