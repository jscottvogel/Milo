import { ImplementFeatureInput, LlmResponse } from "./types";
import { RepoIngester } from "./ingester";
import { LlmClient } from "./llm";
import { FileWriter } from "./writer";
import { ReviewManager } from "./reviewer";

export class ImplementFeatureTool {
  private llmClient: LlmClient;
  private reviewManager: ReviewManager;

  constructor() {
    this.llmClient = new LlmClient();
    this.reviewManager = new ReviewManager();
  }

  /**
   * Handles the implement_feature tool execution
   */
  public async handle(input: ImplementFeatureInput): Promise<any> {
    // 1. Handle existing review session
    if (input.session_id) {
      const session = this.reviewManager.getSession(input.session_id);
      if (!session) {
        throw new Error(`Review session ${input.session_id} not found or expired.`);
      }

      if (input.approved === true) {
        const writer = new FileWriter(session.repo_path);
        
        try {
          writer.applyChanges(session.changes);
          const ingester = new RepoIngester(session.repo_path);
          const repoContext = ingester.ingest(""); // Dummy prompt for validation
          const warnings = writer.validate(repoContext, session.changes);
          
          this.reviewManager.resolveSession(input.session_id);
          
          return {
            plan: session.plan,
            changes: session.changes,
            status: "applied",
            summary: `Successfully applied ${session.changes.length} changes from session ${input.session_id}.`,
            warnings,
          };
        } catch (error: any) {
          writer.rollback();
          throw new Error(`Failed to apply changes: ${error.message}. All changes rolled back.`);
        }
      } else if (input.approved === false) {
        this.reviewManager.resolveSession(input.session_id);
        return {
          plan: session.plan,
          changes: session.changes,
          status: "rejected",
          summary: `Changes for session ${input.session_id} were rejected.`,
          warnings: [],
        };
      } else {
        throw new Error("Must provide 'approved: true' or 'approved: false' to resolve a session.");
      }
    }

    // 2. Start a new implementation
    const ingester = new RepoIngester(input.repo_path);
    const repoContext = ingester.ingest(input.feature_prompt);

    // Filter to target_files if specified
    if (input.target_files && input.target_files.length > 0) {
      const targetPaths = new Set(input.target_files.map((p: string) => p.replace(/\\\\/g, "/")));
      repoContext.files = repoContext.files.filter((f) => 
        input.target_files!.some((t: string) => f.path.replace(/\\\\/g, "/").startsWith(t.replace(/\\\\/g, "/")))
      );
    }

    const llmResponse = await this.llmClient.planAndImplement(repoContext, input.feature_prompt);
    const writer = new FileWriter(input.repo_path);

    // Attach diffs for review/dry_run
    const changesWithDiffs = llmResponse.changes.map(c => {
      const content = (c.action === "create" || c.action === "modify") ? c.content || "" : null;
      return {
        ...c,
        diff: writer.generateDiff(c.file_path, content),
      };
    });

    if (input.dry_run) {
      return {
        plan: llmResponse.plan,
        changes: changesWithDiffs,
        status: "dry_run",
        summary: `Dry run complete. ${changesWithDiffs.length} changes planned.`,
        warnings: [],
      };
    }

    if (input.review_mode) {
      const sessionId = this.reviewManager.createSession(input.repo_path, llmResponse.plan, changesWithDiffs);
      return {
        session_id: sessionId,
        plan: llmResponse.plan,
        changes: changesWithDiffs,
        status: "pending_review",
        summary: `Review mode active. Inspect diffs and call again with session_id '${sessionId}' and approved: true/false.`,
        warnings: [],
      };
    }

    // Direct apply
    try {
      writer.applyChanges(llmResponse.changes);
      const warnings = writer.validate(repoContext, llmResponse.changes);
      
      return {
        plan: llmResponse.plan,
        changes: llmResponse.changes,
        status: "applied",
        summary: `Successfully applied ${llmResponse.changes.length} changes.`,
        warnings,
      };
    } catch (error: any) {
      writer.rollback();
      throw new Error(`Failed to apply changes: ${error.message}. All changes rolled back.`);
    }
  }
}
