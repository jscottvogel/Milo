import { z } from "zod";

/**
 * Input schema for the implement_feature tool
 */
export const ImplementFeatureInputSchema = z.object({
  repo_path: z.string().describe("Absolute path to the local GitHub repo directory"),
  feature_prompt: z.string().describe("Natural language description of the feature to implement"),
  target_files: z.array(z.string()).optional().describe("Specific files/dirs to scope the changes to"),
  review_mode: z.boolean().default(false).describe("If true, show diffs and wait for explicit 'approve' or 'reject' before writing any files"),
  dry_run: z.boolean().default(false).describe("If true, return the plan and diffs without writing files. Supersedes review_mode."),
  session_id: z.string().optional().describe("If continuing a review session, provide the session ID"),
  approved: z.boolean().optional().describe("If continuing a review session, whether the changes are approved"),
});

export type ImplementFeatureInput = z.infer<typeof ImplementFeatureInputSchema>;

/**
 * Information extracted from the repository
 */
export interface RepoContext {
  tree: string;
  files: Array<{
    path: string;
    content: string;
  }>;
  language: string;
  framework: string;
  entryPoints: string[];
}

/**
 * Represents a single file change proposed by the LLM
 */
export interface ChangeItem {
  file_path: string;
  action: "create" | "modify" | "delete";
  content?: string;
  reasoning: string;
}

/**
 * The LLM's full response
 */
export interface LlmResponse {
  plan: string[];
  changes: ChangeItem[];
}

/**
 * Represents a pending review session
 */
export interface ReviewSession {
  id: string;
  repo_path: string;
  plan: string[];
  changes: Array<ChangeItem & { diff?: string }>;
  timestamp: number;
}
