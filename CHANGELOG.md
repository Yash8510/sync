# Changelog

All notable changes to **S.Y.N.C.** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Piper TTS synthesis wrapper integration (`models/tts/en_US-amy-medium.onnx`).
- Audio playback response queue and speaking state visualizer animation.
- Local LLM inference integration (Ollama / Llama.cpp) inside `process_utterance()`.
- Wake-word detection engine (*"Hey Kaelo"* / *"Synca"*).

---

## [0.1.0-alpha] - 2026-08-18

### Added
- **Audio Capture Subsystem:** Continuous 16kHz non-blocking microphone stream via `sounddevice` with a 5-second `deque` ring buffer (`audio/capture.py`).
- **Voice Activity Detection:** Silero VAD frame windowing (512-sample frames) with peak confidence probability calculation (`audio/vad.py`).
- **Turn-Taking Controller:** Automatic conversational state tracking and silence verification with configurable threshold ($1.5\text{ s}$) (`audio/turn_taking.py`).
- **Speech-to-Text Pipeline:** Offline transcription engine wrapping `faster-whisper` with CUDA tensor acceleration and VAD pre-filtering (`speech/stt.py`).
- **Spectral Analysis Engine:** 40 FPS Hanning-windowed FFT extracting 16 geometric logarithmic frequency bands ($80\text{--}4000\text{ Hz}$) with asymmetric peak Auto-Gain Control (`ui/main_window.py`).
- **Holographic Floating Orb Widget:** Frameless, translucent, draggable PyQt6 desktop widget with 3-ring parametric wavy particle dynamics coupled to Bass, Mid, and Treble audio bands (`ui/widgets.py`).
- **Event-Driven Architecture:** Asynchronous `EventBus` and `PyQtEventBridge` marshaling background pipeline events into thread-safe Qt signals (`core/event_bus.py`, `ui/bridge.py`).
- **Configuration & Logging:** Centralized YAML configuration loading with immutable dataclass wrapper and dual console/file logging (`core/config.py`, `core/logging_setup.py`).
- **Dependency Management:** Structured `requirements.txt` pinning exact compatible version ranges for GUI, audio capture, STT, VAD, and diagnostic suites.
- **Deep Technical Specifications:** 6 modular documentation guides under `docs/` detailing sampling math, VAD frame geometry, FFT formulas, orb physics, STT tensors, and tri-thread concurrency.

### Fixed
- Fixed Windows PyTorch/PyQt DLL collision memory errors by enforcing pre-import ordering in `main.py`.
- Fixed buffer accumulation bug when draining stale audio chunks across turns in `audio/orchestrator.py`.
- Fixed clean multi-thread shutdown and asyncio task cancellation when closing the PyQt application window.
