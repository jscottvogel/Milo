import { v4 as uuidv4 } from "uuid";
import { ReviewSession, ChangeItem } from "./types";

export class ReviewManager {
  private sessions: Map<string, ReviewSession> = new Map();

  /**
   * Creates a new pending review session
   */
  public createSession(repoPath: string, plan: string[], changes: Array<ChangeItem & { diff?: string }>): string {
    const id = uuidv4();
    this.sessions.set(id, {
      id,
      repo_path: repoPath,
      plan,
      changes,
      timestamp: Date.now(),
    });
    
    // Simple cleanup: remove sessions older than 2 hours
    this.cleanupOldSessions();
    
    return id;
  }

  /**
   * Retrieves a session by ID
   */
  public getSession(id: string): ReviewSession | undefined {
    return this.sessions.get(id);
  }

  /**
   * Resolves a session and removes it
   */
  public resolveSession(id: string): void {
    this.sessions.delete(id);
  }

  /**
   * Cleans up old sessions
   */
  private cleanupOldSessions(): void {
    const now = Date.now();
    const TWO_HOURS = 2 * 60 * 60 * 1000;
    
    for (const [id, session] of this.sessions.entries()) {
      if (now - session.timestamp > TWO_HOURS) {
        this.sessions.delete(id);
      }
    }
  }
}
