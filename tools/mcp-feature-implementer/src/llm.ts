import Anthropic from "@anthropic-ai/sdk";
import { RepoContext, LlmResponse } from "./types";

export class LlmClient {
  private client: Anthropic;

  constructor() {
    this.client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY || "",
    });
  }

  public async planAndImplement(
    repoContext: RepoContext,
    featurePrompt: string
  ): Promise<LlmResponse> {
    const fileContentsStr = repoContext.files
      .map((f) => `--- FILE: ${f.path} ---\n${f.content}\n--------------------`)
      .join("\n\n");

    const systemPrompt = `You are a senior software engineer performing a code change on a real repository.
You will be given a repo structure and feature request.
Respond ONLY with a valid JSON object. No prose, no markdown fences.`;

    const userPrompt = `Repository language/framework: ${repoContext.language} / ${repoContext.framework}

Directory tree:
${repoContext.tree}

Relevant file contents:
${fileContentsStr}

Feature to implement:
${featurePrompt}

Return a JSON object with this exact shape:
{
  "plan": ["step 1", "step 2", ...],
  "changes": [
    {
      "file_path": "relative/path/to/file.ts",
      "action": "create" | "modify" | "delete",
      "content": "full new file content as a string (for create/modify)",
      "reasoning": "why this file needs to change"
    }
  ]
}

Rules:
- file_path must be relative to the repo root
- For 'modify', content must be the COMPLETE new file contents, not a diff
- For 'delete', content can be empty
- Do not modify lock files, .git directory, or binary files
- Preserve existing code style, formatting, and conventions
- If tests exist for modified files, update them too`;

    try {
      const response = await this.client.messages.create({
        model: "claude-sonnet-4-6", // Model ID as specified by prompt
        max_tokens: 8192, // High token limit for large files
        system: systemPrompt,
        messages: [
          { role: "user", content: userPrompt }
        ],
      });

      const textOutput = (response.content[0] as any).text.trim();
      
      try {
        const parsed = JSON.parse(textOutput) as LlmResponse;
        return parsed;
      } catch (err) {
        throw new Error("LLM returned invalid JSON. Output was: " + textOutput.substring(0, 500) + "...");
      }
    } catch (error: any) {
      throw new Error(`Failed to call Anthropic API: ${error.message}`);
    }
  }
}
