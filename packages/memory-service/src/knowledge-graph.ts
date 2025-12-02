/**
 * Knowledge Graph Manager
 *
 * Manages entities, observations, and relations for IRIS memory.
 * Pattern from: agentic-framework/patterns/sqlite-knowledge-graph.md
 */

import type Database from "better-sqlite3";

// ============================================================================
// Types
// ============================================================================

export interface Entity {
  name: string;
  entityType: string;
  observations: string[];
}

export interface Relation {
  from: string;
  to: string;
  relationType: string;
}

export interface KnowledgeGraph {
  entities: Entity[];
  relations: Relation[];
}

interface DbEntity {
  id: string;
  user_id: string;
  name: string;
  entity_type: string;
  created_at: number;
}

interface DbRelation {
  id: string;
  user_id: string;
  from_entity_id: string;
  to_entity_id: string;
  relation_type: string;
  created_at: number;
}

// ============================================================================
// Knowledge Graph Manager
// ============================================================================

export class KnowledgeGraphManager {
  private db: Database.Database;
  private userId: string;

  constructor(db: Database.Database, userId: string) {
    this.db = db;
    this.userId = userId;
  }

  // --------------------------------------------------------------------------
  // Write Operations
  // --------------------------------------------------------------------------

  createEntities(entities: Entity[], isUserEdit = false): Entity[] {
    const created: Entity[] = [];
    const now = Date.now();
    const userEditFlag = isUserEdit ? 1 : 0;

    for (const entity of entities) {
      // Case-insensitive duplicate check
      const existing = this.db.prepare(`
        SELECT id FROM memory_entities
        WHERE user_id = ? AND LOWER(name) = LOWER(?)
      `).get(this.userId, entity.name) as { id: string } | undefined;

      let entityId: string;
      if (existing) {
        entityId = existing.id;
      } else {
        entityId = crypto.randomUUID();
        this.db.prepare(`
          INSERT INTO memory_entities (id, user_id, name, entity_type, created_at, updated_at)
          VALUES (?, ?, ?, ?, ?, ?)
        `).run(entityId, this.userId, entity.name, entity.entityType, now, now);
      }

      // Add observations (skip duplicates)
      for (const obs of entity.observations || []) {
        const obsExists = this.db.prepare(
          `SELECT id FROM memory_observations WHERE entity_id = ? AND LOWER(observation) = LOWER(?)`
        ).get(entityId, obs);
        if (!obsExists) {
          this.db.prepare(`
            INSERT INTO memory_observations (id, entity_id, observation, created_at, updated_at, is_user_edit)
            VALUES (?, ?, ?, ?, ?, ?)
          `).run(crypto.randomUUID(), entityId, obs, now, now, userEditFlag);
        }
      }
      created.push(entity);
    }
    return created;
  }

  createRelations(relations: Relation[]): Relation[] {
    const created: Relation[] = [];
    const now = Date.now();

    for (const rel of relations) {
      const existing = this.db.prepare(`
        SELECT id FROM memory_relations
        WHERE user_id = ? AND LOWER(from_entity_id) = LOWER(?) AND LOWER(to_entity_id) = LOWER(?)
        AND LOWER(relation_type) = LOWER(?)
      `).get(this.userId, rel.from, rel.to, rel.relationType);

      if (!existing) {
        this.db.prepare(`
          INSERT INTO memory_relations (id, user_id, from_entity_id, to_entity_id, relation_type, created_at)
          VALUES (?, ?, ?, ?, ?, ?)
        `).run(crypto.randomUUID(), this.userId, rel.from, rel.to, rel.relationType, now);
        created.push(rel);
      }
    }
    return created;
  }

  addObservations(
    observations: { entityName: string; contents: string[] }[],
    isUserEdit = false
  ): { entityName: string; added: string[] }[] {
    const results: { entityName: string; added: string[] }[] = [];
    const now = Date.now();
    const userEditFlag = isUserEdit ? 1 : 0;

    for (const { entityName, contents } of observations) {
      const entity = this.db.prepare(`
        SELECT id FROM memory_entities WHERE user_id = ? AND LOWER(name) = LOWER(?)
      `).get(this.userId, entityName) as { id: string } | undefined;

      if (!entity) continue;

      const added: string[] = [];
      for (const content of contents) {
        const exists = this.db.prepare(
          `SELECT id FROM memory_observations WHERE entity_id = ? AND LOWER(observation) = LOWER(?)`
        ).get(entity.id, content);
        if (!exists) {
          this.db.prepare(
            `INSERT INTO memory_observations (id, entity_id, observation, created_at, updated_at, is_user_edit)
             VALUES (?, ?, ?, ?, ?, ?)`
          ).run(crypto.randomUUID(), entity.id, content, now, now, userEditFlag);
          added.push(content);
        }
      }
      if (added.length > 0) results.push({ entityName, added });
    }
    return results;
  }

  deleteEntities(entityNames: string[]): string[] {
    const deleted: string[] = [];
    for (const name of entityNames) {
      const result = this.db.prepare(`
        DELETE FROM memory_entities WHERE user_id = ? AND LOWER(name) = LOWER(?)
      `).run(this.userId, name);

      if (result.changes > 0) {
        // Cascade: delete relations involving this entity
        this.db.prepare(`
          DELETE FROM memory_relations
          WHERE user_id = ? AND (LOWER(from_entity_id) = LOWER(?) OR LOWER(to_entity_id) = LOWER(?))
        `).run(this.userId, name, name);
        deleted.push(name);
      }
    }
    return deleted;
  }

  deleteObservations(
    deletions: { entityName: string; observations: string[] }[]
  ): { entityName: string; deleted: string[] }[] {
    const results: { entityName: string; deleted: string[] }[] = [];
    for (const { entityName, observations } of deletions) {
      const entity = this.db.prepare(`
        SELECT id FROM memory_entities WHERE user_id = ? AND LOWER(name) = LOWER(?)
      `).get(this.userId, entityName) as { id: string } | undefined;

      if (!entity) continue;

      const deleted: string[] = [];
      for (const obs of observations) {
        const result = this.db.prepare(
          `DELETE FROM memory_observations WHERE entity_id = ? AND LOWER(observation) = LOWER(?)`
        ).run(entity.id, obs);
        if (result.changes > 0) deleted.push(obs);
      }
      if (deleted.length > 0) results.push({ entityName, deleted });
    }
    return results;
  }

  deleteRelations(relations: Relation[]): Relation[] {
    const deleted: Relation[] = [];
    for (const rel of relations) {
      const result = this.db.prepare(`
        DELETE FROM memory_relations
        WHERE user_id = ? AND LOWER(from_entity_id) = LOWER(?) AND LOWER(to_entity_id) = LOWER(?)
        AND LOWER(relation_type) = LOWER(?)
      `).run(this.userId, rel.from, rel.to, rel.relationType);
      if (result.changes > 0) deleted.push(rel);
    }
    return deleted;
  }

  // --------------------------------------------------------------------------
  // Read Operations
  // --------------------------------------------------------------------------

  readGraph(): KnowledgeGraph {
    const entityRows = this.db.prepare(`
      SELECT e.*, GROUP_CONCAT(o.observation, '||') as observations
      FROM memory_entities e
      LEFT JOIN memory_observations o ON e.id = o.entity_id
      WHERE e.user_id = ?
      GROUP BY e.id ORDER BY e.created_at DESC
    `).all(this.userId) as (DbEntity & { observations: string | null })[];

    const entities: Entity[] = entityRows.map((r) => ({
      name: r.name,
      entityType: r.entity_type,
      observations: r.observations ? r.observations.split("||") : [],
    }));

    const relationRows = this.db.prepare(`
      SELECT * FROM memory_relations WHERE user_id = ? ORDER BY created_at DESC
    `).all(this.userId) as DbRelation[];

    const relations: Relation[] = relationRows.map((r) => ({
      from: r.from_entity_id,
      to: r.to_entity_id,
      relationType: r.relation_type,
    }));

    return { entities, relations };
  }

  searchNodes(query: string, limit = 10): Entity[] {
    const q = query.toLowerCase();
    const words = q.split(/\s+/).filter((w) => w.length > 2);

    const rows = this.db.prepare(`
      SELECT e.*, GROUP_CONCAT(o.observation, '||') as observations
      FROM memory_entities e
      LEFT JOIN memory_observations o ON e.id = o.entity_id
      WHERE e.user_id = ?
      GROUP BY e.id
    `).all(this.userId) as (DbEntity & { observations: string | null })[];

    const scored = rows.map((r) => {
      const name = r.name.toLowerCase();
      const type = r.entity_type.toLowerCase();
      const obs = (r.observations || "").toLowerCase();
      let score = 0;
      if (name.includes(q)) score += 10;
      if (type.includes(q)) score += 5;
      if (obs.includes(q)) score += 8;
      for (const w of words) {
        if (name.includes(w)) score += 3;
        if (obs.includes(w)) score += 2;
      }
      return { r, score };
    });

    return scored
      .filter((s) => s.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map((s) => ({
        name: s.r.name,
        entityType: s.r.entity_type,
        observations: s.r.observations ? s.r.observations.split("||") : [],
      }));
  }

  openNodes(names: string[]): KnowledgeGraph {
    const entities: Entity[] = [];
    const relSet = new Set<string>();
    const relations: Relation[] = [];

    for (const name of names) {
      const row = this.db.prepare(`
        SELECT e.*, GROUP_CONCAT(o.observation, '||') as observations
        FROM memory_entities e
        LEFT JOIN memory_observations o ON e.id = o.entity_id
        WHERE e.user_id = ? AND LOWER(e.name) = LOWER(?)
        GROUP BY e.id
      `).get(this.userId, name) as (DbEntity & { observations: string | null }) | undefined;

      if (row) {
        entities.push({
          name: row.name,
          entityType: row.entity_type,
          observations: row.observations ? row.observations.split("||") : [],
        });

        const rels = this.db.prepare(`
          SELECT * FROM memory_relations
          WHERE user_id = ? AND (LOWER(from_entity_id) = LOWER(?) OR LOWER(to_entity_id) = LOWER(?))
        `).all(this.userId, name, name) as DbRelation[];

        for (const rel of rels) {
          const key = `${rel.from_entity_id}|${rel.relation_type}|${rel.to_entity_id}`;
          if (!relSet.has(key)) {
            relSet.add(key);
            relations.push({
              from: rel.from_entity_id,
              to: rel.to_entity_id,
              relationType: rel.relation_type,
            });
          }
        }
      }
    }
    return { entities, relations };
  }

  // --------------------------------------------------------------------------
  // User Edit Operations
  // --------------------------------------------------------------------------

  getUserEdits(): { entityName: string; observation: string; createdAt: number }[] {
    const rows = this.db.prepare(`
      SELECT e.name as entity_name, o.observation, o.created_at
      FROM memory_observations o
      JOIN memory_entities e ON o.entity_id = e.id
      WHERE e.user_id = ? AND o.is_user_edit = 1
      ORDER BY o.created_at DESC
    `).all(this.userId) as {
      entity_name: string;
      observation: string;
      created_at: number;
    }[];

    return rows.map((r) => ({
      entityName: r.entity_name,
      observation: r.observation,
      createdAt: r.created_at,
    }));
  }

  deleteUserEdit(entityName: string, observation: string): boolean {
    const entity = this.db.prepare(`
      SELECT id FROM memory_entities WHERE user_id = ? AND LOWER(name) = LOWER(?)
    `).get(this.userId, entityName) as { id: string } | undefined;

    if (!entity) return false;

    const result = this.db.prepare(`
      DELETE FROM memory_observations
      WHERE entity_id = ? AND LOWER(observation) = LOWER(?) AND is_user_edit = 1
    `).run(entity.id, observation);

    return result.changes > 0;
  }

  getUserEditCount(): number {
    const result = this.db.prepare(`
      SELECT COUNT(*) as count
      FROM memory_observations o
      JOIN memory_entities e ON o.entity_id = e.id
      WHERE e.user_id = ? AND o.is_user_edit = 1
    `).get(this.userId) as { count: number };

    return result.count;
  }

  // --------------------------------------------------------------------------
  // Summary Operations
  // --------------------------------------------------------------------------

  saveSummary(summary: string): void {
    const now = Date.now();
    const graph = this.readGraph();
    const entityCount = graph.entities.length;
    const observationCount = graph.entities.reduce((sum, e) => sum + e.observations.length, 0);

    const existing = this.db.prepare(`
      SELECT id FROM memory_summaries WHERE user_id = ?
    `).get(this.userId) as { id: string } | undefined;

    if (existing) {
      this.db.prepare(`
        UPDATE memory_summaries
        SET summary = ?, generated_at = ?, entity_count = ?, observation_count = ?
        WHERE id = ?
      `).run(summary, now, entityCount, observationCount, existing.id);
    } else {
      this.db.prepare(`
        INSERT INTO memory_summaries (id, user_id, summary, generated_at, entity_count, observation_count)
        VALUES (?, ?, ?, ?, ?, ?)
      `).run(crypto.randomUUID(), this.userId, summary, now, entityCount, observationCount);
    }
  }

  getSummary(): { summary: string; generatedAt: number; entityCount: number; observationCount: number } | null {
    const row = this.db.prepare(`
      SELECT summary, generated_at, entity_count, observation_count
      FROM memory_summaries WHERE user_id = ?
    `).get(this.userId) as {
      summary: string;
      generated_at: number;
      entity_count: number;
      observation_count: number;
    } | undefined;

    if (!row) return null;

    return {
      summary: row.summary,
      generatedAt: row.generated_at,
      entityCount: row.entity_count,
      observationCount: row.observation_count,
    };
  }

  isSummaryStale(): boolean {
    const cached = this.getSummary();
    if (!cached) return true;

    const graph = this.readGraph();
    const currentEntityCount = graph.entities.length;
    const currentObsCount = graph.entities.reduce((sum, e) => sum + e.observations.length, 0);

    return cached.entityCount !== currentEntityCount || cached.observationCount !== currentObsCount;
  }

  deleteSummary(): boolean {
    const result = this.db.prepare(`
      DELETE FROM memory_summaries WHERE user_id = ?
    `).run(this.userId);

    return result.changes > 0;
  }
}
