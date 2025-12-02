/**
 * Knowledge Graph Manager Tests
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { initializeMemoryDb, closeMemoryDb, getMemoryManager } from "./database.js";
import { KnowledgeGraphManager } from "./knowledge-graph.js";
import fs from "fs";

const TEST_DB_PATH = "./test-iris.db";
const TEST_USER_ID = "test-user-123";

describe("KnowledgeGraphManager", () => {
  let manager: KnowledgeGraphManager;

  beforeEach(() => {
    // Clean up any existing test database
    if (fs.existsSync(TEST_DB_PATH)) {
      fs.unlinkSync(TEST_DB_PATH);
    }
    if (fs.existsSync(`${TEST_DB_PATH}-wal`)) {
      fs.unlinkSync(`${TEST_DB_PATH}-wal`);
    }
    if (fs.existsSync(`${TEST_DB_PATH}-shm`)) {
      fs.unlinkSync(`${TEST_DB_PATH}-shm`);
    }

    initializeMemoryDb(TEST_DB_PATH);
    manager = getMemoryManager(TEST_USER_ID);
  });

  afterEach(() => {
    closeMemoryDb();
    // Clean up test database
    if (fs.existsSync(TEST_DB_PATH)) {
      fs.unlinkSync(TEST_DB_PATH);
    }
    if (fs.existsSync(`${TEST_DB_PATH}-wal`)) {
      fs.unlinkSync(`${TEST_DB_PATH}-wal`);
    }
    if (fs.existsSync(`${TEST_DB_PATH}-shm`)) {
      fs.unlinkSync(`${TEST_DB_PATH}-shm`);
    }
  });

  describe("createEntities", () => {
    it("should create a new entity", () => {
      const created = manager.createEntities([
        {
          name: "The Armada",
          entityType: "fleet",
          observations: ["Has 5 ships", "Based in sector 7"],
        },
      ]);

      expect(created).toHaveLength(1);
      expect(created[0].name).toBe("The Armada");
      expect(created[0].entityType).toBe("fleet");
    });

    it("should not create duplicate entities (case-insensitive)", () => {
      manager.createEntities([{ name: "The Armada", entityType: "fleet", observations: [] }]);
      manager.createEntities([{ name: "the armada", entityType: "fleet", observations: ["New observation"] }]);

      const graph = manager.readGraph();
      expect(graph.entities).toHaveLength(1);
      expect(graph.entities[0].observations).toContain("New observation");
    });

    it("should track user edits separately", () => {
      manager.createEntities(
        [{ name: "Commander Sam", entityType: "person", observations: ["The fleet commander"] }],
        true // isUserEdit
      );

      const edits = manager.getUserEdits();
      expect(edits).toHaveLength(1);
      expect(edits[0].entityName).toBe("Commander Sam");
      expect(edits[0].observation).toBe("The fleet commander");
    });
  });

  describe("createRelations", () => {
    it("should create relationships between entities", () => {
      manager.createEntities([
        { name: "Sam", entityType: "person", observations: [] },
        { name: "The Armada", entityType: "fleet", observations: [] },
      ]);

      const created = manager.createRelations([{ from: "Sam", to: "The Armada", relationType: "commands" }]);

      expect(created).toHaveLength(1);
      expect(created[0].relationType).toBe("commands");
    });

    it("should not create duplicate relations", () => {
      manager.createRelations([{ from: "Sam", to: "The Armada", relationType: "commands" }]);
      const second = manager.createRelations([{ from: "Sam", to: "The Armada", relationType: "commands" }]);

      expect(second).toHaveLength(0);
    });
  });

  describe("searchNodes", () => {
    beforeEach(() => {
      manager.createEntities([
        { name: "The Armada", entityType: "fleet", observations: ["Has 5 ships", "Mining operation"] },
        { name: "Star Cruiser", entityType: "ship", observations: ["Part of The Armada"] },
        { name: "Commander Sam", entityType: "person", observations: ["Commands The Armada"] },
      ]);
    });

    it("should find entities by name", () => {
      const results = manager.searchNodes("armada");
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].name).toBe("The Armada");
    });

    it("should find entities by observation content", () => {
      const results = manager.searchNodes("mining");
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].name).toBe("The Armada");
    });

    it("should return empty array for no matches", () => {
      const results = manager.searchNodes("nonexistent");
      expect(results).toHaveLength(0);
    });
  });

  describe("openNodes", () => {
    beforeEach(() => {
      manager.createEntities([
        { name: "Sam", entityType: "person", observations: ["Fleet commander"] },
        { name: "The Armada", entityType: "fleet", observations: ["5 ships"] },
      ]);
      manager.createRelations([{ from: "Sam", to: "The Armada", relationType: "commands" }]);
    });

    it("should return entity with its relations", () => {
      const graph = manager.openNodes(["Sam"]);

      expect(graph.entities).toHaveLength(1);
      expect(graph.entities[0].name).toBe("Sam");
      expect(graph.relations).toHaveLength(1);
      expect(graph.relations[0].relationType).toBe("commands");
    });
  });

  describe("deleteEntities", () => {
    it("should delete entity and cascade to relations", () => {
      manager.createEntities([
        { name: "Sam", entityType: "person", observations: [] },
        { name: "The Armada", entityType: "fleet", observations: [] },
      ]);
      manager.createRelations([{ from: "Sam", to: "The Armada", relationType: "commands" }]);

      const deleted = manager.deleteEntities(["Sam"]);

      expect(deleted).toContain("Sam");
      const graph = manager.readGraph();
      expect(graph.entities).toHaveLength(1);
      expect(graph.relations).toHaveLength(0);
    });
  });

  describe("summaries", () => {
    it("should save and retrieve summaries", () => {
      manager.createEntities([{ name: "Test", entityType: "concept", observations: ["A test entity"] }]);

      manager.saveSummary("This is a test summary about the user's memory.");

      const summary = manager.getSummary();
      expect(summary).not.toBeNull();
      expect(summary!.summary).toBe("This is a test summary about the user's memory.");
      expect(summary!.entityCount).toBe(1);
    });

    it("should detect stale summaries", () => {
      manager.createEntities([{ name: "Test", entityType: "concept", observations: [] }]);
      manager.saveSummary("Summary");

      // Add more entities
      manager.createEntities([{ name: "Test2", entityType: "concept", observations: [] }]);

      expect(manager.isSummaryStale()).toBe(true);
    });
  });
});
