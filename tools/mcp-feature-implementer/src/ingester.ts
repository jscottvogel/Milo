import fs from "fs";
import path from "path";
import ignore, { Ignore } from "ignore";
import { RepoContext } from "./types";

const MAX_CHARS = 320000; // ~80,000 tokens (4 chars/token)

const ALWAYS_INCLUDE = [
  "README.md",
  "README.txt",
  "package.json",
  "tsconfig.json",
  "requirements.txt",
  "pyproject.toml",
  "Cargo.toml",
  "go.mod",
  "index.ts",
  "index.js",
  "main.ts",
  "main.py",
  "src/index.ts",
  "src/main.ts"
];

export class RepoIngester {
  private repoPath: string;
  private ig: Ignore;

  constructor(repoPath: string) {
    this.repoPath = repoPath;
    this.ig = ignore();
    this.loadGitignore();
  }

  /**
   * Loads .gitignore rules if present
   */
  private loadGitignore(): void {
    const gitignorePath = path.join(this.repoPath, ".gitignore");
    if (fs.existsSync(gitignorePath)) {
      const content = fs.readFileSync(gitignorePath, "utf-8");
      this.ig.add(content);
    }
    // Always ignore standard noisy dirs
    this.ig.add(["node_modules", ".git", "dist", "build", "out", "coverage", ".venv", "venv"]);
  }

  /**
   * Recursively walks the directory structure
   */
  private walk(dir: string, base: string = ""): string[] {
    let results: string[] = [];
    const list = fs.readdirSync(dir);

    for (const file of list) {
      const relativePath = path.join(base, file);
      // Skip if ignored
      if (this.ig.ignores(relativePath.replace(/\\/g, "/"))) continue;

      const fullPath = path.join(dir, file);
      const stat = fs.statSync(fullPath);

      if (stat && stat.isDirectory()) {
        results = results.concat(this.walk(fullPath, relativePath));
      } else {
        results.push(relativePath);
      }
    }
    return results;
  }

  /**
   * Detect language and framework based on files present
   */
  private detectStack(files: string[]): { language: string; framework: string } {
    let language = "Unknown";
    let framework = "Unknown";

    const hasFile = (name: string) => files.some((f) => path.basename(f) === name);

    if (hasFile("package.json")) {
      language = "JavaScript/TypeScript";
      if (hasFile("next.config.js") || hasFile("next.config.mjs")) framework = "Next.js";
      else if (hasFile("vite.config.ts") || hasFile("vite.config.js")) framework = "Vite/React";
      else framework = "Node.js";

      if (hasFile("tsconfig.json")) language = "TypeScript";
    } else if (hasFile("requirements.txt") || hasFile("pyproject.toml")) {
      language = "Python";
      if (hasFile("manage.py")) framework = "Django";
      else if (files.some((f) => f.includes("FastAPI") || f.includes("fastapi"))) framework = "FastAPI";
      else framework = "Unknown Python";
    }

    return { language, framework };
  }

  /**
   * Generates a string representation of the directory tree
   */
  private generateTree(files: string[]): string {
    const tree: any = {};
    for (const file of files) {
      const parts = file.replace(/\\/g, "/").split("/");
      let current = tree;
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        if (!current[part]) {
          current[part] = i === parts.length - 1 ? null : {};
        }
        current = current[part];
      }
    }

    const formatTree = (node: any, prefix: string = ""): string => {
      let result = "";
      const keys = Object.keys(node);
      for (let i = 0; i < keys.length; i++) {
        const key = keys[i];
        const isLast = i === keys.length - 1;
        result += prefix + (isLast ? "└── " : "├── ") + key + "\n";
        if (node[key] !== null) {
          result += formatTree(node[key], prefix + (isLast ? "    " : "│   "));
        }
      }
      return result;
    };

    return formatTree(tree);
  }

  /**
   * Calculate a simple relevance score based on keyword matching
   */
  private getRelevanceScore(content: string, featurePrompt: string): number {
    const keywords = featurePrompt
      .toLowerCase()
      .split(/\W+/)
      .filter((w) => w.length > 3);
    
    let score = 0;
    const lowerContent = content.toLowerCase();
    for (const kw of keywords) {
      if (lowerContent.includes(kw)) score += 1;
    }
    return score;
  }

  /**
   * Reads files, respecting the token limit and prioritizing relevance
   */
  public ingest(featurePrompt: string): RepoContext {
    const allFiles = this.walk(this.repoPath);
    const { language, framework } = this.detectStack(allFiles);
    const tree = this.generateTree(allFiles);

    const fileObjects: { path: string; content: string; score: number; isPriority: boolean }[] = [];

    // First pass: Read all files to get their sizes and basic relevance
    for (const relPath of allFiles) {
      const fullPath = path.join(this.repoPath, relPath);
      // Skip very large files quickly
      const stat = fs.statSync(fullPath);
      if (stat.size > 500000) continue; // Skip files > 500KB

      // Skip common binary extensions
      const ext = path.extname(relPath).toLowerCase();
      if ([".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz"].includes(ext)) {
        continue;
      }

      try {
        const content = fs.readFileSync(fullPath, "utf-8");
        // Ensure it's somewhat readable text (simple check)
        if (content.includes("\0")) continue; // Contains null bytes, likely binary

        const isPriority = ALWAYS_INCLUDE.some(p => relPath.replace(/\\/g, "/").endsWith(p));
        const score = this.getRelevanceScore(content, featurePrompt);

        fileObjects.push({ path: relPath, content, score, isPriority });
      } catch (err) {
        // Skip unreadable files
      }
    }

    // Sort by priority first, then relevance score, then alphabetically
    fileObjects.sort((a, b) => {
      if (a.isPriority && !b.isPriority) return -1;
      if (!a.isPriority && b.isPriority) return 1;
      if (a.score !== b.score) return b.score - a.score;
      return a.path.localeCompare(b.path);
    });

    // Pack into context respecting limits
    let currentChars = 0;
    const selectedFiles: { path: string; content: string }[] = [];

    for (const f of fileObjects) {
      if (currentChars + f.content.length > MAX_CHARS) {
        // If it's a priority file and we are over, maybe we truncate? 
        // For simplicity, just stop adding.
        break;
      }
      selectedFiles.push({ path: f.path, content: f.content });
      currentChars += f.content.length;
    }

    const entryPoints = allFiles.filter(f => 
      f.endsWith("index.ts") || f.endsWith("index.js") || f.endsWith("main.ts") || f.endsWith("main.py")
    );

    return {
      tree,
      files: selectedFiles,
      language,
      framework,
      entryPoints,
    };
  }
}
