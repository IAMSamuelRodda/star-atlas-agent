/**
 * IRIS Voice Service
 *
 * WebSocket server for real-time voice interaction.
 * Bridges browser audio to Python voice backend (faster-whisper + Chatterbox).
 *
 * Architecture:
 * ```
 * Browser (WebRTC/MediaRecorder)
 *     ↓ WebSocket
 * voice-service (Node.js)
 *     ↓ HTTP
 * voice-backend (Python FastAPI)
 *     ↓
 * faster-whisper (STT) / Chatterbox (TTS)
 * ```
 *
 * Usage:
 * ```typescript
 * import { VoiceWebSocketServer } from "@iris/voice-service";
 *
 * const server = new VoiceWebSocketServer({
 *   port: 8002,
 *   backendUrl: "http://localhost:8001",
 * });
 * ```
 */

export const VERSION = "0.1.0";

// Types
export type {
  ClientMessage,
  ServerMessage,
  TranscribeResponse,
  SynthesizeRequest,
  HealthResponse,
  VoiceSession,
  VoiceServiceConfig,
} from "./types.js";

export { DEFAULT_CONFIG } from "./types.js";

// Voice Client
export { VoiceClient, getVoiceClient } from "./voice-client.js";

// WebSocket Server
export { VoiceWebSocketServer } from "./websocket-server.js";

// Main entry point for standalone server
if (import.meta.url === `file://${process.argv[1]}`) {
  const port = parseInt(process.env.VOICE_WS_PORT || "8002", 10);
  const backendUrl = process.env.VOICE_BACKEND_URL || "http://localhost:8001";

  console.log("Starting IRIS Voice Service...");
  console.log(`  WebSocket port: ${port}`);
  console.log(`  Backend URL: ${backendUrl}`);

  const server = new (await import("./websocket-server.js")).VoiceWebSocketServer({
    port,
    backendUrl,
  });

  // Graceful shutdown
  process.on("SIGINT", async () => {
    console.log("\nShutting down...");
    await server.close();
    process.exit(0);
  });

  process.on("SIGTERM", async () => {
    console.log("\nShutting down...");
    await server.close();
    process.exit(0);
  });
}
