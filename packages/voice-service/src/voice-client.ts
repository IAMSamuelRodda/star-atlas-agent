/**
 * Voice Backend Client
 *
 * HTTP client for communicating with the Python voice-backend service.
 * Handles STT (transcription) and TTS (synthesis) requests.
 */

import type { HealthResponse, SynthesizeRequest, TranscribeResponse, VoiceServiceConfig } from "./types.js";

export class VoiceClient {
  private baseUrl: string;

  constructor(config: Pick<VoiceServiceConfig, "backendUrl">) {
    this.baseUrl = config.backendUrl;
  }

  /**
   * Check if the voice backend is healthy.
   */
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json() as Promise<HealthResponse>;
  }

  /**
   * Transcribe audio to text.
   *
   * @param audioBuffer - WAV audio data
   * @param language - Optional language hint
   * @returns Transcription result
   */
  async transcribe(audioBuffer: Buffer, language?: string): Promise<TranscribeResponse> {
    const formData = new FormData();

    // Create a Blob from the buffer
    const audioBlob = new Blob([audioBuffer], { type: "audio/wav" });
    formData.append("audio", audioBlob, "audio.wav");

    if (language) {
      formData.append("language", language);
    }

    const response = await fetch(`${this.baseUrl}/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Transcription failed: ${error}`);
    }

    return response.json() as Promise<TranscribeResponse>;
  }

  /**
   * Synthesize speech from text.
   *
   * @param request - Synthesis parameters
   * @returns WAV audio data
   */
  async synthesize(request: SynthesizeRequest): Promise<Buffer> {
    const response = await fetch(`${this.baseUrl}/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Synthesis failed: ${error}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    return Buffer.from(arrayBuffer);
  }

  /**
   * Synthesize speech with streaming response.
   *
   * @param request - Synthesis parameters
   * @yields PCM audio chunks
   */
  async *synthesizeStream(request: SynthesizeRequest): AsyncGenerator<Buffer> {
    const response = await fetch(`${this.baseUrl}/synthesize/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Streaming synthesis failed: ${error}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        yield Buffer.from(value);
      }
    } finally {
      reader.releaseLock();
    }
  }
}

// Singleton instance
let clientInstance: VoiceClient | null = null;

export function getVoiceClient(backendUrl: string = "http://localhost:8001"): VoiceClient {
  if (!clientInstance) {
    clientInstance = new VoiceClient({ backendUrl });
  }
  return clientInstance;
}
