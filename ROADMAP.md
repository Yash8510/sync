# S.Y.N.C. — Development Roadmap

This document outlines the strategic milestones and technical roadmap for **S.Y.N.C. (Synthetic Neural Companion)**.

---

## 🎯 Milestone Checklist

### 🏁 Phase 1: Acoustic Perception & Visualizer (v0.1.0-alpha) — *Completed*
- [x] Continuous microphone capture at $16\text{ kHz}$ with 5-second ring buffer.
- [x] Silero VAD neural frame slicing (512-sample stride) with speech confidence scoring.
- [x] Turn-taking state machine with silence duration timeout ($1.5\text{ s}$).
- [x] Offline Faster-Whisper STT with CUDA acceleration (`distil-large-v3.5` / `base`).
- [x] PyQt6 16-band logarithmic FFT frequency analyzer with asymmetric peak AGC ($40\text{ FPS}$).
- [x] 3D holographic floating orb widget with 3-ring wavy particle animations (Bass/Mid/Treble).
- [x] Thread-safe event bus and PyQt signal bridge.
- [x] Complete modular mathematical specifications under `docs/`.

---

### 🔊 Phase 2: Vocal Synthesis (v0.2.0-alpha) — *In Progress*
- [ ] Piper TTS engine wrapper (`models/tts/en_US-amy-medium.onnx`).
- [ ] Non-blocking audio playback output stream (`sounddevice.OutputStream`).
- [ ] Visualizer feedback animation for assistant vocal reply states (Speaking mode).
- [ ] Dynamic volume and speech rate control in `config/default.yaml`.

---

### 🧠 Phase 3: Cognitive Intelligence & LLM Router (v0.3.0-alpha)
- [ ] Local LLM brain integration (Ollama / Llama.cpp / llama-cpp-python).
- [ ] Conversational memory buffer (rolling chat context & system persona).
- [ ] Intent classifier for system commands (launch applications, web search, system stats).
- [ ] Safety confirmation dialogs for dangerous OS actions (`SafetyBridge`).

---

### 🎙️ Phase 4: Wake-Word & Desktop Refinement (v0.4.0-beta)
- [ ] Offline wake-word detection engine (*"Hey Kaelo"* / *"Synca"* / openWakeWord).
- [ ] Expand `MainWindow` UI with message transcript feed and interactive audio controls.
- [ ] System tray integration (minimize to tray, global shortcut hotkeys).
- [ ] Settings panel for mic selection, STT model switching, and VAD sensitivity sliders.

---

### 🚀 Phase 5: Production Release (v1.0.0)
- [ ] Comprehensive unit and integration test suite (`pytest`, mock audio streams).
- [ ] Standalone Windows installer / portable executable packaging (PyInstaller / Nuitka).
- [ ] Benchmarked CPU / GPU VRAM resource optimization.
- [ ] Public open-source launch.
