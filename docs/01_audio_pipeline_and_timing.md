# Module 01: Audio Pipeline, Buffer Math & Timing Specification

## 1. Acoustic Ingestion Parameters

The audio capture subsystem ([`audio/capture.py`](../audio/capture.py)) operates as an uncompressed, continuous pulse-code modulated (PCM) stream via `sounddevice` / PortAudio C-driver bindings.

```
                  ┌────────────────────────────────────────────────────────┐
                  │                Microphone Audio Stream                 │
                  │  Sample Rate (fs): 16,000 Hz | Channels: 1 (Mono)      │
                  │  Bit Depth: 32-bit Floating Point (np.float32)         │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   Chunk Block (N = 1024)  │
                               │   Δt = 64.0 ms per chunk  │
                               └─────────────┬─────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      │                                             │
                      ▼                                             ▼
        ┌───────────────────────────┐                 ┌───────────────────────────┐
        │  Ring Buffer (deque)      │                 │  Utterance Queue (Queue)  │
        │  Capacity: 78 Chunks (5s) │                 │  Thread-Safe FIFO Buffer  │
        └───────────────────────────┘                 └───────────────────────────┘
```

### Mathematical Definitions

| Parameter | Symbol | Formula | Standard Value |
| :--- | :---: | :---: | :---: |
| **Sampling Frequency** | $f_s$ | — | $16,000\text{ Hz}$ ($16\text{ kHz}$) |
| **Channel Count** | $C$ | Mono | $1$ |
| **Chunk Block Size** | $N$ | — | $1,024\text{ samples}$ |
| **Chunk Duration** | $\Delta t_{\text{chunk}}$ | $\frac{N}{f_s}$ | $\frac{1024}{16000} = 0.064\text{ s} = 64.0\text{ ms}$ |
| **Chunk Generation Rate** | $R_{\text{chunk}}$ | $\frac{f_s}{N}$ | $\frac{16000}{1024} = 15.625\text{ chunks/sec}$ |
| **Ring Buffer Duration** | $T_{\text{buf}}$ | — | $5.0\text{ s}$ |
| **Ring Buffer Capacity** | $B_{\text{max}}$ | $\lfloor \frac{f_s \cdot T_{\text{buf}}}{N} \rfloor$ | $\lfloor \frac{16000 \times 5}{1024} \rfloor = 78\text{ chunks}$ |
| **Ring Buffer Sample Count** | $S_{\text{max}}$ | $B_{\text{max}} \cdot N$ | $78 \times 1024 = 79,872\text{ samples}$ ($4.992\text{ s}$) |

---

## 2. Ingestion & Producer-Consumer Synchronization

Audio frames arrive from the high-priority OS audio callback thread and are dispatched through two pathways:

1. **Stateful Ring Buffer (`deque(maxlen=78)`):**
   * Protected by `threading.Lock()`.
   * Holds the most recent 5 seconds of audio.
   * Provides non-blocking reverse slice retrieval for the UI visualizer via [`get_recent_audio()`](../audio/capture.py).

2. **Thread-Safe Queue (`queue.Queue[np.ndarray]`):**
   * Dispatched via `_on_chunk(chunk)` registered in [`AudioSpeechPipeline`](../audio/orchestrator.py).
   * Decouples the PortAudio callback thread from the `asyncio` turn-taking state machine.

---

## 3. Utterance Accumulation Bounds & Phase Analysis

The orchestrator executes a two-phase capture state machine during [`get_user_utterance()`](../audio/orchestrator.py):

```
       [ IDLE ] ──(Audio In)──> [ PHASE 1: Awaiting Speech ]
                                       │
                         VAD Trigger (Speech Detected)
                                       │
                                       ▼
                                [ PHASE 2: Accumulating Utterance ]
                                       │
                         Silence Threshold Reached (Δt >= 1.5s)
                                       │
                                       ▼
                                [ Concatenate & Transcribe ]
```

### Accumulation Duration Formula

Let:
* $T_{\text{speech}}$ = Duration of user vocalization (seconds)
* $T_{\text{silence}} = 1.5\text{ s}$ (Silence threshold before utterance is declared complete)
* $T_{\text{timeout}} = 30.0\text{ s}$ (Global maximum utterance window)

$$\text{Total Accumulated Duration } T_{\text{total}} = \min\left(T_{\text{speech}} + T_{\text{silence}}, \, T_{\text{timeout}}\right)$$
$$\text{Accumulated Chunk Count } K = \lceil T_{\text{total}} \cdot R_{\text{chunk}} \rceil = \lceil T_{\text{total}} \times 15.625 \rceil$$
$$\text{Total Audio Samples } S_{\text{total}} = K \cdot N = K \times 1024$$

---

## 4. Scenario Metrics Reference

| Metric | Minimum Case (Transient Click / Syllable) | Standard Sentence ($3.0\text{ s}$ speech) | Maximum Window (Timeout Boundary) |
| :--- | :--- | :--- | :--- |
| **$T_{\text{speech}}$** | $\approx 0.05\text{ s}$ | $3.00\text{ s}$ | $28.50\text{ s}$ |
| **$T_{\text{silence}}$** | $1.50\text{ s}$ | $1.50\text{ s}$ | $1.50\text{ s}$ |
| **Total Duration ($T_{\text{total}}$)** | $\approx 1.55\text{ s}$ | $4.50\text{ s}$ | $30.00\text{ s}$ |
| **Chunks Accumulated ($K$)** | $24\text{ chunks}$ | $70\text{ to } 71\text{ chunks}$ | $468\text{ to } 469\text{ chunks}$ |
| **Sample Array Size ($S_{\text{total}}$)** | $24,576\text{ samples}$ | $72,704\text{ samples}$ | $480,256\text{ samples}$ |
| **Memory Footprint (float32)** | $98.3\text{ KB}$ | $290.8\text{ KB}$ | $1.92\text{ MB}$ |

---

## 5. Ring Buffer Reverse Traversal Algorithm

To avoid concatenating all 78 chunks when the visualizer requests the last $M = 1024$ samples:

```python
# Traversal cost: O(k) where k = ceil(M / chunk_size) <= 2 chunks, rather than O(B_max)
chunks_needed = []
samples_accumulated = 0

for chunk in reversed(self.buffer):
    chunks_needed.append(chunk)
    samples_accumulated += len(chunk)
    if samples_accumulated >= num_samples:
        break

chunks_needed.reverse()
concatenated = np.concatenate(chunks_needed)
return concatenated[-num_samples:]
```
