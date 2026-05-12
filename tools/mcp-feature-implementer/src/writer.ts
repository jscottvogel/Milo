import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import * as Diff from "diff";
import { ChangeItem, RepoContext } from "./types";

export class FileWriter {
  private repoPath: string;
  private backups: Map<string, string | null> = new Map(); // null means file didn't exist before

  constructor(repoPath: string) {
    this.repoPath = path.resolve(repoPath);
  }

  /**
   * Prevents path traversal
   */
  private resolveAndValidatePath(relPath: string): string {
    const fullPath = path.resolve(this.repoPath, relPath);
    if (!fullPath.startsWith(this.repoPath)) {
      throw new Error(`Path traversal detected: ${relPath}`);
    }
    return fullPath;
  }

  /**
   * Backups a file before modifying
   */
  private backupFile(fullPath: string): void {
    if (this.backups.has(fullPath)) return; // already backed up

    if (fs.existsSync(fullPath)) {
      this.backups.set(fullPath, fs.readFileSync(fullPath, "utf-8"));
    } else {
      this.backups.set(fullPath, null);
    }
  }

  /**
   * Rolls back all changes using the backups
   */
  public rollback(): void {
    for (const [fullPath, originalContent] of this.backups.entries()) {
      if (originalContent === null) {
        if (fs.existsSync(fullPath)) {
          fs.unlinkSync(fullPath);
        }
      } else {
        fs.writeFileSync(fullPath, originalContent, "utf-8");
      }
    }
    this.backups.clear();
  }

  /**
   * Writes a file atomically
   */
  private writeAtomic(fullPath: string, content: string): void {
    const dir = path.dirname(fullPath);
    fs.mkdirSync(dir, { recursive: true });

    const tempPath = `${fullPath}.tmp.${Date.now()}`;
    fs.writeFileSync(tempPath, content, "utf-8");
    fs.renameSync(tempPath, fullPath);
  }

  /**
   * Generates a unified diff
   */
  public generateDiff(relPath: string, newContent: string | null): string {
    const fullPath = this.resolveAndValidatePath(relPath);
    const oldContent = fs.existsSync(fullPath) ? fs.readFileSync(fullPath, "utf-8") : "";
    const safeNewContent = newContent === null ? "" : newContent;
    
    return Diff.createTwoFilesPatch(
      relPath,
      relPath,
      oldContent,
      safeNewContent,
      "Original",
      "Modified"
    );
  }

  /**
   * Applies the changes
   */
  public applyChanges(changes: ChangeItem[]): void {
    for (const change of changes) {
      const fullPath = this.resolveAndValidatePath(change.file_path);
      this.backupFile(fullPath);

      if (change.action === "create" || change.action === "modify") {
        if (change.content === undefined) {
          throw new Error(`Missing content for file ${change.file_path}`);
        }
        this.writeAtomic(fullPath, change.content);
      } else if (change.action === "delete") {
        if (fs.existsSync(fullPath)) {
          fs.unlinkSync(fullPath);
        }
      }
    }
  }

  /**
   * Runs post-write validation based on framework/language
   */
  public validate(repoContext: RepoContext, changes: ChangeItem[]): string[] {
    const warnings: string[] = [];

    // TypeScript validation
    if (repoContext.language === "TypeScript") {
      const tsconfigPath = path.join(this.repoPath, "tsconfig.json");
      if (fs.existsSync(tsconfigPath)) {
        try {
          execSync("npx tsc --noEmit", { cwd: this.repoPath, stdio: "pipe" });
        } catch (error: any) {
          warnings.push(`TypeScript validation failed: ${error.stdout?.toString() || error.message}`);
        }
      }
    }

    // Python validation
    if (repoContext.language === "Python") {
      for (const change of changes) {
        if (change.file_path.endsWith(".py") && change.action !== "delete") {
          try {
            execSync(`python -m py_compile ${change.file_path}`, { cwd: this.repoPath, stdio: "pipe" });
          } catch (error: any) {
            warnings.push(`Python validation failed for ${change.file_path}: ${error.stderr?.toString() || error.message}`);
          }
        }
      }
    }

    return warnings;
  }
}
