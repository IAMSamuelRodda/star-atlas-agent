# Adaptive Verbosity Control System

> **Status**: Design Riff (2025-12-05)
> **Author**: Sam (original concept)
> **Related**: Narrator module, Voice styles

## Overview

A multi-layered verbosity control system that dynamically adjusts response length based on explicit commands, implicit user behavior, and style settings.

## Design Principles

### Layer 1: Style (System Prompt) - Baseline

The voice style system provides the baseline verbosity ceiling:
- **Concise**: Hard cap on length
- **Normal/Neutral**: Maximum dynamic range
- **Verbose/Immersive**: Allows longer responses

System prompts set expectations but shouldn't completely override user signals.

### Layer 2: Explicit Commands - Highest Priority

Direct user instructions override all other signals:

| Signal | Intent | Response |
|--------|--------|----------|
| "give me the quick version" | Concise with key details | Short, actionable |
| "give me the details, leave nothing out" | Comprehensive | Long, thorough |
| "summarize" / "tldr" | Extreme brevity | Bullet points |
| "explain like I'm 5" | Simple but complete | Medium, accessible |

These explicit commands should be **seriously weighted** by the model.

### Layer 3: Implicit Mirroring - Subtle Adjustment

When no explicit command is given, infer verbosity from user behavior:

**Terse User Signals (→ short responses):**
- One-word commands
- Short 1-sentence messages
- Action-oriented language ("do X", "run Y")
- Indicates: Fast action required, no fluff

**Verbose User Signals (→ longer responses):**
- Rambling messages
- Multiple paragraphs over several turns
- Exploratory language ("I was thinking...", "what if...")
- Indicates: User wants to be heard, detail is welcome

**The Affirmation Insight:**
When a user is being wordy/rambling, they often:
1. Want to be **heard and understood** first
2. Need **affirmation** that their input was received
3. Then appreciate a **thoughtful, detailed response**

This suggests a two-phase response pattern:
1. Brief acknowledgment ("Got it - you're dealing with X, Y, Z")
2. Detailed response that addresses their points

## Priority Hierarchy

```
Explicit Command > Style Setting > Implicit Mirroring
     (highest)                        (lowest)

Exception: Explicit command within a neutral style gets maximum effect
```

## Edge Cases

1. **Short explicit override**: "give me more details" from a terse user
   - Honor the explicit request, don't assume they want brevity

2. **Style conflict**: Concise style + user asks for details
   - Explicit command wins, but respect style's format preferences

3. **Mixed signals**: Verbose message asking for quick answer
   - Honor the explicit "quick" request

## Implementation Considerations

- Lightweight heuristics (word count, punctuation density, keywords)
- No additional LLM inference for detection
- Rolling window of last 3-5 messages for implicit signals
- Temporal decay: Recent messages weighted higher

## Open Questions

1. How to handle voice vs text differently? Voice naturally shorter.
2. Should narrator verbosity sync with response verbosity?
3. Memory: Should we learn user preferences across sessions?

---

## Related: Streaming Architecture Considerations

> *Riff session 2025-12-05*

### The Streaming Hypothesis

If we stream aggressively enough, the two-tier response strategy (fast ack + full response) may become unnecessary. The real response arrives fast enough to fill the cognitive gap.

**Current two-tier flow:**
```
User finishes → STT (180ms) → Fast ack (130ms) → TTS (42ms) = ~350ms to "Got it"
                    ↓
              Smart model thinking → TTS → Full response (~2-3s)
```

**Proposed streaming flow:**
```
User speaking → STT streaming partial → LLM receiving context
User finishes → VAD detects end → LLM immediately generates
             → TTS streams first tokens → User hears response ~200-400ms
```

### Key Architectural Changes Needed

1. **VAD (Voice Activity Detection)** - Critical for knowing when to trigger LLM generation
   - Silero VAD v5 (~50ms detection)
   - Enables interruption handling
   - Separate design riff needed

2. **Streaming with overlapping operations**
   - STT streams partials while user speaks
   - LLM receives context BEFORE user finishes
   - TTS starts on first token, not complete response

3. **RealtimeTTS + RealtimeSTT pattern**
   - Audio chunk streaming over WebSocket
   - Local models for fast path
   - Cloud LLMs (Claude) for deep reasoning via separate WebSocket
   - Context accumulates continuously

### The Context-First Insight

> "It's all about context management - give the model as much context as soon as possible and remove wait times on user inputs."

If the LLM has:
- The conversation history
- The user's partial utterance (streaming)
- Recent tool results / narrator context

...it can start "pre-thinking" before the user even finishes. When VAD signals end-of-speech, the LLM finalizes and streams immediately.

### Interruption Handling with VAD

Smart VAD management enables clean context despite interruptions:

```
User: "What's the status of my—"
IRIS: [starts generating]
User: "—actually, just the fuel levels"
VAD: [detects new speech, signals interrupt]
IRIS: [stops generation, appends correction to context, regenerates]
```

The context includes the false start. The model understands what happened.

### Does This Kill Two-Tier?

**Maybe for fast local models.** If Qwen 7B can start streaming in <200ms, you hear real content fast enough.

**Not for cloud models.** Claude Sonnet has network latency + queue time. The first token might be 800ms-2s away. Fast ack still valuable here.

**Hybrid approach:**
- Local model: Pure streaming, no ack needed
- Cloud model: Fast local ack while waiting for first cloud token
- Narrator: Decides whether to vocalize based on expected latency

### Interruption Context Handling

When user interrupts IRIS mid-response, **don't truncate context - annotate it**.

**The problem:**
```
IRIS generating: "Three updates. First, Alpha docked. Second, fuel critical. Third, repairs done."
User interrupts after: "Second, fuel crit—"
```

**Wrong approach:** Truncate context to what was spoken. Model loses knowledge.

**Right approach:** Annotate the interruption:

```typescript
interface InterruptionEvent {
  intendedResponse: string;      // full generated response
  spokenUpTo: string;            // parsed from TTS playhead position
  interruptedAtWord: number;     // word/character position
  userInterruption: string;      // what they said
}
```

**Prompt injection pattern:**
> "Note: Your previous response was interrupted by the user after '...fuel crit—'. They only heard up to that point. Your full intended response was: [X]. Their interruption: [Y]"

**Benefits:**
1. Model retains full knowledge of what it intended to say
2. Model understands social context (being cut off)
3. Model can offer to complete: "Fuel's at 15%. I also had an update about repairs - want it?"
4. Enables natural phrases: "As I was saying...", "To finish that thought..."

**Future consideration:** Ambient audio cue (subtle chime) as alternative to verbal acknowledgment during cloud model latency gaps.

---

## Model-Specific System Prompts

> *Noted 2025-12-05*

Different models respond better to different prompt structures. Consider:

1. **Prompt library per model family**
   - Qwen prompts optimized for Qwen 2.5 variants
   - Llama prompts for Llama family
   - Claude prompts for Anthropic models

2. **Dynamic prompt loading**
   - When narrator seat loads a new model, load matching system prompt
   - Fallback to generic prompt if no specific one exists

3. **Optimization review needed**
   - Audit all current system prompts
   - A/B test variations per model
   - Track which prompts yield best verbosity control per model

---

## STT Optimization Notes

> *Investigation 2025-12-05*

### Current State (Batch Mode)
Optimized faster-whisper with beam_size=1:
- 2s audio: 22-28ms transcription (well under 50ms target)
- 6s audio: 55-58ms transcription
- Architecture: Batch mode (transcribe after VAD detects end-of-speech)
- No streaming needed for current latency requirements

### Future: Custom Streaming Wrapper
If sub-20ms latency becomes critical, build custom streaming wrapper:

**Architecture**:
```
Audio stream → 15-20ms chunk buffer → Forward pass every 100ms → Partials
            → VAD end detection → Final in ~10-15ms
```

**Components**:
1. **Silero VAD v5** (~50ms end detection)
   - Already integrated in RealtimeSTT prototype
   - Standalone version lighter weight

2. **Custom faster-whisper streaming**:
   - Roll forward buffer (keep last 30s context)
   - Process 15-20ms chunks
   - Forward pass every 100ms for partials
   - Emit final on VAD end trigger

3. **Chunk management**:
   - Ring buffer for incoming audio
   - Overlap windows for smoother transcription
   - Timestamp alignment for partials

**Trade-offs**:
- Pros: Maximum speed (<15ms theoretical), no portaudio dependency
- Cons: ~2-4 hours implementation, more complex debugging
- When: Only if batch mode latency becomes a measurable bottleneck

**Prototype location**: `src/stt_streaming.py` (RealtimeSTT-based)

---

*This is a living design document. Implementation TBD.*
