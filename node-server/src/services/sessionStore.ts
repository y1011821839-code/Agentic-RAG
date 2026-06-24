/**
 * SQLite 会话存储 — 从 Python 迁移到 Node.js
 * 优势：Node.js 的 better-sqlite3 是同步 API，性能更好
 */
import Database from 'better-sqlite3';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import { fileURLToPath } from 'url';
import type { ChatMessage, SessionInfo } from '../types.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.resolve(__dirname, '..', '..', 'sessions.db');

class SessionStore {
  private db: Database.Database;

  constructor() {
    this.db = new Database(DB_PATH);
    this.db.pragma('journal_mode = WAL');
    this.init();
  }

  private init() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT DEFAULT '新对话',
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT DEFAULT (datetime('now', 'localtime'))
      )
    `);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
      )
    `);
    this.db.exec(`CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id)`);
  }

  // =========== 会话 ===========

  createSession(title: string = '新对话'): string {
    const id = uuidv4().replace(/-/g, '').slice(0, 12);
    this.db.prepare('INSERT INTO sessions (id, title) VALUES (?, ?)').run(id, title);
    return id;
  }

  listSessions(): SessionInfo[] {
    return this.db
      .prepare('SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC')
      .all() as SessionInfo[];
  }

  getSession(sessionId: string): SessionInfo | null {
    const row = this.db.prepare('SELECT * FROM sessions WHERE id = ?').get(sessionId) as SessionInfo | undefined;
    return row ?? null;
  }

  deleteSession(sessionId: string) {
    this.db.prepare('DELETE FROM sessions WHERE id = ?').run(sessionId);
  }

  touchSession(sessionId: string) {
    this.db
      .prepare("UPDATE sessions SET updated_at = datetime('now', 'localtime') WHERE id = ?")
      .run(sessionId);
  }

  // =========== 消息 ===========

  saveMessage(sessionId: string, role: string, content: string) {
    this.db
      .prepare('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)')
      .run(sessionId, role, content);
    this.touchSession(sessionId);
  }

  saveExchange(sessionId: string, question: string, answer: string) {
    const insert = this.db.prepare('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)');
    const tx = this.db.transaction(() => {
      insert.run(sessionId, 'user', question);
      insert.run(sessionId, 'assistant', answer);
    });
    tx();
    this.touchSession(sessionId);
  }

  getMessages(sessionId: string): ChatMessage[] {
    return this.db
      .prepare('SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC')
      .all(sessionId) as ChatMessage[];
  }

  getHistoryForLLM(sessionId: string): ChatMessage[] {
    return this.db
      .prepare(
        `SELECT role, content FROM (
          SELECT role, content, id FROM messages
          WHERE session_id = ?
          ORDER BY id DESC LIMIT 20
        ) ORDER BY id ASC`
      )
      .all(sessionId) as ChatMessage[];
  }

  close() {
    this.db.close();
  }
}

// 全局单例
export const sessionStore = new SessionStore();