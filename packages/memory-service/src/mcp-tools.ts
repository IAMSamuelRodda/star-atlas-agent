/**
 * Memory MCP Tool Handlers
 *
 * Aligned with Anthropic's MCP Memory Server tool naming.
 * Tools: create/delete entities/relations/observations, read_graph, search_nodes, open_nodes
 *
 * Pattern from: agentic-framework/patterns/sqlite-knowledge-graph.md
 */

import { getMemoryManager } from "./database.js";
import type { Entity, Relation, KnowledgeGraph } from "./knowledge-graph.js";

// ============================================================================
// Tool Definitions
// ============================================================================

export const memoryToolDefinitions = [
  {
    name: "create_entities",
    description: `Create new entities in IRIS's memory (people, organizations, fleets, concepts, etc.).
Use when the user mentions something worth remembering about their Star Atlas experience.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        entities: {
          type: "array",
          items: {
            type: "object",
            properties: {
              name: { type: "string", description: "Entity name (e.g., 'The Armada', 'Commander Sam')" },
              entityType: {
                type: "string",
                description: "Type: person, organization, fleet, ship, location, concept, event",
              },
              observations: {
                type: "array",
                items: { type: "string" },
                description: "Initial facts about this entity",
              },
            },
            required: ["name", "entityType"],
          },
          description: "Entities to create",
        },
        isUserEdit: {
          type: "boolean",
          description: "True if user explicitly requested this memory (e.g., 'remember that...')",
        },
      },
      required: ["entities"],
    },
  },
  {
    name: "create_relations",
    description: `Create relationships between entities (e.g., "commands", "owns", "located_at").
Both entities should exist first. Use active voice for relation types.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        relations: {
          type: "array",
          items: {
            type: "object",
            properties: {
              from: { type: "string", description: "Source entity name" },
              to: { type: "string", description: "Target entity name" },
              relationType: {
                type: "string",
                description: "Relationship type in active voice (e.g., 'commands', 'owns', 'mines_at')",
              },
            },
            required: ["from", "to", "relationType"],
          },
          description: "Relations to create",
        },
      },
      required: ["relations"],
    },
  },
  {
    name: "add_observations",
    description: `Add facts/observations to existing entities.
Use when the user shares new information about something IRIS already knows.
Set isUserEdit=true when user explicitly asks to remember something.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        observations: {
          type: "array",
          items: {
            type: "object",
            properties: {
              entityName: { type: "string", description: "Entity to add observations to" },
              contents: { type: "array", items: { type: "string" }, description: "Facts to add" },
            },
            required: ["entityName", "contents"],
          },
          description: "Observations to add",
        },
        isUserEdit: {
          type: "boolean",
          description: "True if user explicitly requested this memory. Default: false",
        },
      },
      required: ["observations"],
    },
  },
  {
    name: "delete_entities",
    description: `Remove entities and all their observations. Use with caution.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        entityNames: {
          type: "array",
          items: { type: "string" },
          description: "Names of entities to delete",
        },
      },
      required: ["entityNames"],
    },
  },
  {
    name: "delete_observations",
    description: `Remove specific observations from entities.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        deletions: {
          type: "array",
          items: {
            type: "object",
            properties: {
              entityName: { type: "string", description: "Entity name" },
              observations: { type: "array", items: { type: "string" }, description: "Observations to remove" },
            },
            required: ["entityName", "observations"],
          },
          description: "Observations to delete",
        },
      },
      required: ["deletions"],
    },
  },
  {
    name: "delete_relations",
    description: `Remove relationships between entities.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        relations: {
          type: "array",
          items: {
            type: "object",
            properties: {
              from: { type: "string" },
              to: { type: "string" },
              relationType: { type: "string" },
            },
            required: ["from", "to", "relationType"],
          },
          description: "Relations to delete",
        },
      },
      required: ["relations"],
    },
  },
  {
    name: "read_graph",
    description: `Read the entire knowledge graph for this user.
Use to get an overview of everything IRIS remembers about the user.`,
    inputSchema: {
      type: "object" as const,
      properties: {},
    },
  },
  {
    name: "search_nodes",
    description: `Search for entities by name or observation content.
ALWAYS call this before answering questions about the user's fleet, preferences, or history.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Search query" },
        limit: { type: "number", description: "Max results (default: 10)" },
      },
      required: ["query"],
    },
  },
  {
    name: "open_nodes",
    description: `Get specific entities by name with their relations.
Use when you need complete context about known entities.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        names: {
          type: "array",
          items: { type: "string" },
          description: "Entity names to retrieve",
        },
      },
      required: ["names"],
    },
  },
  {
    name: "get_memory_summary",
    description: `Get a prose summary of what IRIS remembers about the user.
Use when user asks "what do you know about me?" or similar.`,
    inputSchema: {
      type: "object" as const,
      properties: {},
    },
  },
  {
    name: "save_memory_summary",
    description: `Save a prose summary of the user's memory graph.
Call after generating a summary to cache it.`,
    inputSchema: {
      type: "object" as const,
      properties: {
        summary: {
          type: "string",
          description: "Prose summary of the memory graph (2-5 paragraphs)",
        },
      },
      required: ["summary"],
    },
  },
];

// ============================================================================
// Formatting Helpers
// ============================================================================

function formatEntity(e: Entity): string {
  const obs =
    e.observations.length > 0 ? `\n  Observations:\n${e.observations.map((o) => `    - ${o}`).join("\n")}` : "";
  return `- **${e.name}** (${e.entityType})${obs}`;
}

function formatRelation(r: Relation): string {
  return `- ${r.from} → *${r.relationType}* → ${r.to}`;
}

function formatGraph(graph: KnowledgeGraph): string {
  if (graph.entities.length === 0 && graph.relations.length === 0) {
    return "No memories stored yet.";
  }

  let output = "";
  if (graph.entities.length > 0) {
    output += `**Entities (${graph.entities.length}):**\n${graph.entities.map(formatEntity).join("\n")}\n`;
  }
  if (graph.relations.length > 0) {
    output += `\n**Relations (${graph.relations.length}):**\n${graph.relations.map(formatRelation).join("\n")}`;
  }
  return output;
}

// ============================================================================
// Tool Result Type
// ============================================================================

export interface ToolResult {
  content: { type: "text"; text: string }[];
  isError?: boolean;
}

// ============================================================================
// Tool Execution
// ============================================================================

export function executeMemoryTool(userId: string, toolName: string, args: Record<string, unknown>): ToolResult {
  try {
    const manager = getMemoryManager(userId);

    switch (toolName) {
      case "create_entities": {
        const { entities, isUserEdit } = args as { entities: Entity[]; isUserEdit?: boolean };
        const created = manager.createEntities(entities, isUserEdit || false);
        return {
          content: [
            {
              type: "text",
              text: `Created ${created.length} entities:\n${created.map(formatEntity).join("\n")}`,
            },
          ],
        };
      }

      case "create_relations": {
        const { relations } = args as { relations: Relation[] };
        const created = manager.createRelations(relations);
        if (created.length === 0) {
          return {
            content: [{ type: "text", text: "No new relations created (may already exist or entities not found)." }],
          };
        }
        return {
          content: [
            {
              type: "text",
              text: `Created ${created.length} relations:\n${created.map(formatRelation).join("\n")}`,
            },
          ],
        };
      }

      case "add_observations": {
        const { observations, isUserEdit } = args as {
          observations: { entityName: string; contents: string[] }[];
          isUserEdit?: boolean;
        };
        const results = manager.addObservations(observations, isUserEdit || false);
        if (results.length === 0) {
          return {
            content: [{ type: "text", text: "No observations added (entities not found or already exist)." }],
          };
        }
        const editLabel = isUserEdit ? " (user edit)" : "";
        const output = results.map((r) => `**${r.entityName}**: ${r.added.length} added${editLabel}`).join("\n");
        return {
          content: [{ type: "text", text: `Added observations:\n${output}` }],
        };
      }

      case "delete_entities": {
        const { entityNames } = args as { entityNames: string[] };
        const deleted = manager.deleteEntities(entityNames);
        return {
          content: [
            {
              type: "text",
              text: deleted.length > 0 ? `Deleted ${deleted.length} entities: ${deleted.join(", ")}` : "No entities found to delete.",
            },
          ],
        };
      }

      case "delete_observations": {
        const { deletions } = args as { deletions: { entityName: string; observations: string[] }[] };
        const results = manager.deleteObservations(deletions);
        if (results.length === 0) {
          return {
            content: [{ type: "text", text: "No observations deleted." }],
          };
        }
        const output = results.map((r) => `**${r.entityName}**: ${r.deleted.length} removed`).join("\n");
        return {
          content: [{ type: "text", text: `Deleted observations:\n${output}` }],
        };
      }

      case "delete_relations": {
        const { relations } = args as { relations: Relation[] };
        const deleted = manager.deleteRelations(relations);
        return {
          content: [
            {
              type: "text",
              text:
                deleted.length > 0
                  ? `Deleted ${deleted.length} relations:\n${deleted.map(formatRelation).join("\n")}`
                  : "No relations found to delete.",
            },
          ],
        };
      }

      case "read_graph": {
        const graph = manager.readGraph();
        return {
          content: [{ type: "text", text: formatGraph(graph) }],
        };
      }

      case "search_nodes": {
        const { query, limit } = args as { query: string; limit?: number };
        const entities = manager.searchNodes(query, limit || 10);
        if (entities.length === 0) {
          return {
            content: [{ type: "text", text: `No memories found matching "${query}".` }],
          };
        }
        return {
          content: [
            {
              type: "text",
              text: `**Search results for "${query}":**\n${entities.map(formatEntity).join("\n")}`,
            },
          ],
        };
      }

      case "open_nodes": {
        const { names } = args as { names: string[] };
        const graph = manager.openNodes(names);
        if (graph.entities.length === 0) {
          return {
            content: [{ type: "text", text: `No entities found: ${names.join(", ")}` }],
          };
        }
        return {
          content: [{ type: "text", text: formatGraph(graph) }],
        };
      }

      case "get_memory_summary": {
        const cached = manager.getSummary();
        const isStale = manager.isSummaryStale();
        const userEditCount = manager.getUserEditCount();

        if (!cached) {
          const graph = manager.readGraph();
          if (graph.entities.length === 0) {
            return {
              content: [
                {
                  type: "text",
                  text: "No memories stored yet. I haven't learned anything about you.",
                },
              ],
            };
          }
          return {
            content: [
              {
                type: "text",
                text: `**Summary not yet generated.**\n\nI have ${graph.entities.length} entities with ${graph.entities.reduce((s, e) => s + e.observations.length, 0)} observations stored.\n\nTo generate a summary, call \`read_graph\` to see the full memory, then call \`save_memory_summary\` with a prose summary.`,
              },
            ],
          };
        }

        const staleNote = isStale ? "\n\n_Note: Memory has changed since this summary was generated. Consider regenerating._" : "";
        const editNote = userEditCount > 0 ? `\n\n_${userEditCount} user edit(s) tracked._` : "";

        return {
          content: [
            {
              type: "text",
              text: `**Memory Summary**\n\n${cached.summary}${editNote}${staleNote}\n\n_Last updated: ${new Date(cached.generatedAt).toLocaleString()}_`,
            },
          ],
        };
      }

      case "save_memory_summary": {
        const { summary } = args as { summary: string };
        if (!summary || summary.trim().length < 10) {
          return {
            content: [
              {
                type: "text",
                text: "Error: Summary must be at least 10 characters.",
              },
            ],
            isError: true,
          };
        }
        manager.saveSummary(summary.trim());
        return {
          content: [
            {
              type: "text",
              text: "Memory summary saved successfully.",
            },
          ],
        };
      }

      default:
        return {
          content: [{ type: "text", text: `Unknown memory tool: ${toolName}` }],
          isError: true,
        };
    }
  } catch (error) {
    console.error(`Memory tool error (${toolName}):`, error);
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
        },
      ],
      isError: true,
    };
  }
}
