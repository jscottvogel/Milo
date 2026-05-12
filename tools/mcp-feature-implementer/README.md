# MCP Feature Implementer

An MCP (Model Context Protocol) tool server that autonomously implements features in local codebases using Claude.

## Features

- **Autonomous Implementation**: Give it a local repository path and a feature prompt, and it will plan and execute the changes.
- **Smart Ingestion**: Automatically detects the framework, respects `.gitignore`, and intelligently selects the most relevant files while staying within context limits.
- **Review Mode**: View unified diffs of proposed changes and explicitly approve or reject them before they are written.
- **Dry Run**: Generate an implementation plan and diffs without touching the filesystem.
- **Safe Execution**: Atomic file writes, path traversal prevention, and in-memory rollback if anything fails.
- **Validation**: Automatically runs `tsc --noEmit` or `python -m py_compile` to catch syntax errors immediately after writing.

## Setup

1. Install dependencies:
   \`\`\`bash
   pnpm install
   # or npm install
   \`\`\`

2. Build the project:
   \`\`\`bash
   npm run build
   \`\`\`

## Registration

Add the following to your MCP client configuration (e.g., `mcp_config.json`):

\`\`\`json
{
  "mcpServers": {
    "feature-implementer": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-feature-implementer/dist/index.js"],
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
      }
    }
  }
}
\`\`\`

## Usage flow

The server exposes a single tool: \`implement_feature\`.

**Review Mode Flow Diagram:**

1. Call the tool with \`review_mode: true\`:
   \`implement_feature({ repo_path, feature_prompt, review_mode: true })\`
   *Returns:* \`{ status: 'pending_review', session_id, plan, changes (with diffs) }\`

2. After reviewing the diffs in your client, approve the changes:
   \`implement_feature({ session_id: "uuid", approved: true })\`
   *Returns:* \`{ status: 'applied', summary, warnings }\`
