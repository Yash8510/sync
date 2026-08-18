# Module 05: Speech-to-Text (STT) Inference Engine

## 1. Engine Architecture & CTranslate2 Backend

The Speech-to-Text subsystem ([`speech/stt.py`](../speech/stt.py)) wraps `faster-whisper`, a re-implementation of OpenAI's Whisper model utilizing the **CTranslate2** inference engine.

```
 Combined Audio Array (float32, 16kHz Mono)
                     │
                     ▼
          Pre-processing & Rescaling
                     │
                     ▼
  CTranslate2 Execution Graph (CUDA Tensor Core Engine)
  ├── Precision: float32 / float16 / int8_float16
  ├── Encoder: 80-channel Log-Mel Spectrogram Feature Extractor
  └── Decoder: Autoregressive Transformer with Beam Search
                     │
                     ▼
       Segments & Metadata Decoding
       ├── text: " ".join([s.text for s in segments])
       ├── language: Detected ISO-639 code (e.g., "en")
       └── language_probability: Softmax confidence in [0, 1]
```

---

## 2. Input Tensor Normalization

Faster-Whisper expects audio as a 1D contiguous float32 NumPy array normalized to $[-1.0, 1.0]$.

If raw audio originates from 16-bit signed integer PCM (e.g., standard WAV containers in [`ztest/test_audioDataInfo.py`](../ztest/test_audioDataInfo.py)):

$$x_{\text{float32}}[n] = \frac{x_{\text{int16}}[n]}{32768.0}, \quad \forall n \in [0, S_{\text{total}}-1]$$

---

## 3. Inference Parameters & VAD Filtering

Inference is invoked via:

```python
segments, info = self.model.transcribe(
    audio=audio,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500)
)
```

### Decoding & Beam Search Configuration

| Parameter | Type | Default Value | Technical Role |
| :--- | :---: | :---: | :--- |
| **`device`** | `str` | `"cuda"` | Routes tensor calculations to NVIDIA GPU. |
| **`compute_type`** | `str` | `"float32"` / `"float16"` | Precision format for Transformer layer weights and activations. |
| **`vad_filter`** | `bool` | `True` | Strips leading/trailing/intermittent silence chunks before transformer encoder pass. |
| **`beam_size`** | `int` | `5` | Breadth of beam search hypotheses maintained during autoregressive decoding. |
| **`temperature`** | `float` | `0.0` | Greedy argmax decoding (temperature fallback triggered if compression ratio > 2.4). |

---

## 4. Local Model Storage & Performance Hierarchy

All model weights are stored entirely offline under `models/stt/`:

```
models/stt/
├── models--Systran--faster-whisper-tiny/
├── models--Systran--faster-whisper-tiny.en/
├── models--Systran--faster-whisper-small/
├── models--Systran--faster-whisper-small.en/
├── models--Systran--faster-whisper-base/
├── models--Systran--faster-whisper-base.en/
├── models--mobiuslabsgmbh--faster-whisper-large-v3-turbo/
└── models--distil-whisper--distil-large-v3.5-ct2/
```

### Model Performance Comparison Matrix

| Model Identifier | Parameter Count | VRAM (float16) | Relative Speed | Real-Time Factor (RTF) | Optimal Use Case |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`tiny.en`** | $39\text{ M}$ | $\approx 400\text{ MB}$ | $32\times$ | $\approx 0.02$ | Ultra-low latency voice commands |
| **`base.en`** | $74\text{ M}$ | $\approx 600\text{ MB}$ | $16\times$ | $\approx 0.04$ | General conversational desktop commands |
| **`small.en`** | $244\text{ M}$ | $\approx 1.2\text{ GB}$ | $6\times$ | $\approx 0.09$ | Balanced accuracy / latency |
| **`distil-large-v3.5`** | $756\text{ M}$ | $\approx 2.5\text{ GB}$ | $4.5\times$ | $\approx 0.12$ | **Default:** High accuracy, multi-lingual |
| **`large-v3-turbo`** | $809\text{ M}$ | $\approx 3.0\text{ GB}$ | $3.5\times$ | $\approx 0.15$ | Maximum accuracy, complex terminology |
