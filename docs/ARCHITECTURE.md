# AI Teammates Architecture

## 1. Overview: The "Two Brains" Paradigm

Counter-Strike: Condition Zero is a fast-paced tactical shooter where bot aiming, pathfinding, and shooting require sub-millisecond execution. Modern AI language models require hundreds of milliseconds to seconds to formulate answers.

To achieve natural conversational AI without sacrificing game performance, we separate responsibilities into two cooperating systems:

```
+------------------------------------------------------------------------+
|                          CONDITION ZERO ENGINE                         |
|                                                                        |
|  +--------------------+        UDP 27115       +--------------------+  |
|  |     BODY BRAIN     | ---------------------> |    GAME BRIDGE     |  |
|  | (C++ Native Bots)  |   Real-time HL Logs    |  (Log Parser & RCON|  |
|  | Aim, walk, shoot   | <--------------------- |  Command Dispatch) |  |
|  +--------------------+        UDP 27015       +--------------------+  |
+------------------------------------------------------------------------+
                                                           |
                                                           v
+------------------------------------------------------------------------+
|                         PYTHON AI BRAIN SERVICE                        |
|                                                                        |
|  +--------------------+   +-------------------+   +-----------------+  |
|  |    MOOD MANAGER    |   |  MEMORY MANAGER   |   |  BUDGET ENGINE  |  |
|  | (Tilt, Stress, etc)|   |  (Match History)  |   | (Quota Tracker) |  |
|  +--------------------+   +-------------------+   +-----------------+  |
|                                                                        |
|  +--------------------+   +-------------------+   +-----------------+  |
|  |   STT MIC LISTENER |   |  LLM ORCHESTRATOR |   |  VOICE ENGINE   |  |
|  |  (Whisper / PushV) |   | (Gemini / Offline)|   | (4-Tier Audio)  |  |
|  +--------------------+   +-------------------+   +-----------------+  |
+------------------------------------------------------------------------+
                                                           |
                                                           v
                                            +----------------------------+
                                            |   SPATIAL AUDIO PLAYBACK   |
                                            | (Left / Center / Right pan)|
                                            +----------------------------+
```

---

## 2. The 4 Zero-Budget Audio Layers

1. **Layer 1: Local Voice Line Library**:
   - Hundreds of pre-synthesized emotional lines stored locally as `.mp3` files in `voice/library/<teammate>/<situation>_<n>.mp3`.
   - 0ms network latency and 0 cloud cost during gameplay.
   - Distinct emotional delivery for kills, deaths, bomb events, and banter.
2. **Layer 2: Local / Free Live Neural TTS**:
   - When custom conversation is needed, generates dynamic speech on the fly using Edge-TTS with character-specific pitch and speed offsets.
3. **Layer 3: Cloud LLM (Gemini / OpenRouter)**:
   - For open-ended conversation and mic questions. Monitored strictly by the `TalkBudgetManager` so daily free-tier quotas are never exceeded.
4. **Layer 4: Fallback**:
   - If offline or network fails, intelligent local heuristics and standard bot radio commands preserve gameplay integrity without crashing.

---

## 3. Communication Protocols

- **Game -> Brain**: Standard Half-Life log protocol streamed over UDP port `27115`.
- **Brain -> Game**: GoldSrc RCON UDP packet protocol on port `27015`.
- **Player -> Brain**: Non-blocking audio capture via `sounddevice` triggered by global `V` hotkey, transcribed using OpenAI Whisper.
