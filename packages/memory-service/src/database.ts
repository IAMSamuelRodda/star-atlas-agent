/**
 * Database Initialization and Management
 *
 * SQLite database setup with WAL mode and schema migrations.
 * Pattern from: agentic-framework/patterns/sqlite-knowledge-graph.md
 */

import Database from "better-sqlite3";
import { KnowledgeGraphManager } from "./knowledge-graph.js";

let dbInstance: Database.Database | null = null;

/**
 * Initialize the memory database.
 * Creates tables if they don't exist and applies migrations.
 */
export function initializeMemoryDb(dbPath?: string): Database.Database {
  if (dbInstance) return dbInstance;

  const path = dbPath || process.env.IRIS_DATABASE_PATH || "./data/iris.db";
  dbInstance = new Database(path);

  // Performance pragmas
  dbInstance.pragma("journal_mode = WAL"); // Concurrent reads during writes
  dbInstance.pragma("foreign_keys = ON"); // Cascade deletes work properly

  // Create schema
  dbInstance.exec(`
    -- Entities: Named nodes (people, organizations, concepts, etc.)
    CREATE TABLE IF NOT EXISTS memory_entities (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      name TEXT NOT NULL,
      entity_type TEXT NOT NULL DEFAULT 'concept',
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_mem_ent_user ON memory_entities(user_id);

    -- Observations: Facts attached to entities
    CREATE TABLE IF NOT EXISTS memory_observations (
      id TEXT PRIMARY KEY,
      entity_id TEXT NOT NULL,
      observation TEXT NOT NULL,
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL,
      is_user_edit INTEGER NOT NULL DEFAULT 0,
      FOREIGN KEY (entity_id) REFERENCES memory_entities(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_mem_obs_ent ON memory_observations(entity_id);
    CREATE INDEX IF NOT EXISTS idx_mem_obs_user_edit ON memory_observations(is_user_edit);

    -- Relations: Directed edges between entities
    CREATE TABLE IF NOT EXISTS memory_relations (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      from_entity_id TEXT NOT NULL,
      to_entity_id TEXT NOT NULL,
      relation_type TEXT NOT NULL,
      created_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_mem_rel_user ON memory_relations(user_id);

    -- Summaries: Cached prose summaries per user
    CREATE TABLE IF NOT EXISTS memory_summaries (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL UNIQUE,
      summary TEXT NOT NULL,
      generated_at INTEGER NOT NULL,
      entity_count INTEGER NOT NULL DEFAULT 0,
      observation_count INTEGER NOT NULL DEFAULT 0
    );

    -- Conversations: Short-term memory with TTL (Tier 2)
    CREATE TABLE IF NOT EXISTS conversations (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL,
      role TEXT NOT NULL,           -- 'user' or 'assistant'
      content TEXT NOT NULL,
      created_at INTEGER NOT NULL,
      expires_at INTEGER NOT NULL   -- TTL timestamp
    );
    CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
    CREATE INDEX IF NOT EXISTS idx_conv_expires ON conversations(expires_at);

    -- Users: Basic user info for multi-tenancy
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      wallet_address TEXT UNIQUE,   -- Solana wallet (optional)
      email TEXT UNIQUE,            -- Magic link auth (optional)
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_address);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
  `);

  console.log(`[Memory] Initialized: ${path}`);
  return dbInstance;
}

/**
 * Get a KnowledgeGraphManager for a specific user.
 */
export function getMemoryManager(userId: string): KnowledgeGraphManager {
  const db = initializeMemoryDb();
  return new KnowledgeGraphManager(db, userId);
}

/**
 * Close the database connection.
 */
export function closeMemoryDb(): void {
  if (dbInstance) {
    dbInstance.close();
    dbInstance = null;
  }
}

/**
 * Get the raw database instance (for advanced use cases).
 */
export function getDbInstance(): Database.Database | null {
  return dbInstance;
}

// ============================================================================
// Conversation Memory (Tier 2 - Short-Term)
// ============================================================================

const DEFAULT_TTL_MS = 48 * 60 * 60 * 1000; // 48 hours

export interface ConversationMessage {
  id: string;
  userId: string;
  role: "user" | "assistant";
  content: string;
  createdAt: number;
  expiresAt: number;
}

/**
 * Add a message to conversation history.
 */
export function addConversationMessage(
  userId: string,
  role: "user" | "assistant",
  content: string,
  ttlMs = DEFAULT_TTL_MS
): ConversationMessage {
  const db = initializeMemoryDb();
  const now = Date.now();
  const message: ConversationMessage = {
    id: crypto.randomUUID(),
    userId,
    role,
    content,
    createdAt: now,
    expiresAt: now + ttlMs,
  };

  db.prepare(`
    INSERT INTO conversations (id, user_id, role, content, created_at, expires_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).run(message.id, message.userId, message.role, message.content, message.createdAt, message.expiresAt);

  return message;
}

/**
 * Get recent conversation history for a user.
 */
export function getConversationHistory(userId: string, limit = 20): ConversationMessage[] {
  const db = initializeMemoryDb();
  const now = Date.now();

  const rows = db.prepare(`
    SELECT id, user_id, role, content, created_at, expires_at
    FROM conversations
    WHERE user_id = ? AND expires_at > ?
    ORDER BY created_at DESC
    LIMIT ?
  `).all(userId, now, limit) as {
    id: string;
    user_id: string;
    role: string;
    content: string;
    created_at: number;
    expires_at: number;
  }[];

  // Return in chronological order (oldest first)
  return rows
    .map((r) => ({
      id: r.id,
      userId: r.user_id,
      role: r.role as "user" | "assistant",
      content: r.content,
      createdAt: r.created_at,
      expiresAt: r.expires_at,
    }))
    .reverse();
}

/**
 * Clean up expired conversation messages.
 * Should be called periodically (e.g., on app startup or cron).
 */
export function cleanupExpiredConversations(): number {
  const db = initializeMemoryDb();
  const now = Date.now();

  const result = db.prepare(`
    DELETE FROM conversations WHERE expires_at < ?
  `).run(now);

  if (result.changes > 0) {
    console.log(`[Memory] Cleaned up ${result.changes} expired conversations`);
  }

  return result.changes;
}

/**
 * Clear all conversation history for a user.
 */
export function clearConversationHistory(userId: string): number {
  const db = initializeMemoryDb();

  const result = db.prepare(`
    DELETE FROM conversations WHERE user_id = ?
  `).run(userId);

  return result.changes;
}
