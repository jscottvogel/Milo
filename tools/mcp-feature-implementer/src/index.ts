#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { zodToJsonSchema } from "zod-to-json-schema";
import { ImplementFeatureInputSchema, ImplementFeatureInput } from "./types.js";
import { ImplementFeatureTool } from "./tool.js";

const server = new Server(
  {
    name: "mcp-feature-implementer",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const implementFeatureHandler = new ImplementFeatureTool();

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "implement_feature",
        description:
          "Accepts a local repository path and a feature prompt, then uses an LLM to automatically plan and implement the feature by creating or modifying files. Supports dry-run and review-mode workflows.",
        inputSchema: zodToJsonSchema(ImplementFeatureInputSchema),
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request: unknown) => {
  const req = request as { params: { name: string; arguments?: any } };
  if (req.params.name === "implement_feature") {
    try {
      // Validate input
      const input = ImplementFeatureInputSchema.parse(req.params.arguments) as ImplementFeatureInput;

      // Handle the request
      const result = await implementFeatureHandler.handle(input);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
        isError: false,
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: "text",
            text: `Error executing implement_feature: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  throw new Error(`Tool not found: ${request.params.name}`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("mcp-feature-implementer MCP server running on stdio");
}

main().catch((err) => {
  console.error("Fatal error starting server:", err);
  process.exit(1);
});
