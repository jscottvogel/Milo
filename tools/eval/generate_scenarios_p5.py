import os

scenarios = {
    "16_approve.yaml": """name: "Approval Flow"
description: "Agent creates approval, user approves it"
messages:
  - role: "user"
    content: "Send an email to John about the meeting."
expected_tools:
  - "email.draft"
tags: ["approvals"]
""",
    "17_reject.yaml": """name: "Rejection Flow"
description: "Agent creates approval, user rejects it"
messages:
  - role: "user"
    content: "Send an angry email to the team."
expected_tools:
  - "email.draft"
tags: ["approvals"]
""",
    "18_edit_approval.yaml": """name: "Edit Approval Flow"
description: "Agent creates approval, user edits the payload"
messages:
  - role: "user"
    content: "Draft an email."
expected_tools:
  - "email.draft"
tags: ["approvals"]
""",
    "19_autonomy_raise.yaml": """name: "Autonomy Raise"
description: "Agent uses tool without approval because autonomy is auto"
messages:
  - role: "user"
    content: "Do something with storage."
expected_tools:
  - "storage.read"
tags: ["approvals"]
""",
    "20_expiration.yaml": """name: "Approval Expiration"
description: "Agent creates approval that expires"
messages:
  - role: "user"
    content: "Draft an email that we will forget to approve."
expected_tools:
  - "email.draft"
tags: ["approvals"]
"""
}

base_dir = r"C:\Users\j_sco\projects\Milo\Milo\tools\eval\scenarios"
os.makedirs(base_dir, exist_ok=True)

for filename, content in scenarios.items():
    with open(os.path.join(base_dir, filename), "w") as f:
        f.write(content)

print("Created 5 eval scenarios for Phase 5.")
