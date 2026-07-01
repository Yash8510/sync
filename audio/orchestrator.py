"""
main file which manages audio capture, VAD, STT, TTS, intent routing, playback
into a single file
"""

import logging
from typing import Dict, Optional

import numpy as np
import queue as _queue

from audio.capture import AudioCapture
from audio.vad import VADDectector
from core.event_bus import EventBus

logger = logging.getLogger(__name__)


class AudioSpeechPipeline:
    """orchestrate audio capture, VAD, STT, TTS, intent routing, playback"""
    def __init__(
        self,
        event_bus: EventBus,
        speech_cfg: Dict
    ):
        self.event_bus = event_bus
        self.capture = AudioCapture(sample_rate=speech_cfg.get("sample_rate"),
                                    chunk_size=speech_cfg.get("chunk_size"),
                                    buffer_seconds=speech_cfg.get("buffer_seconds"))
        self.vad = VADDectector(sample_rate=speech_cfg.get("sample_rate"))
        self._is_running = False

        # thread-safe queue to pass audio chunk from callback func which is consumed by get_user_utterance()
        self._audio_queue: _queue.Queue[np.ndarray] = _queue.Queue()

    async def start_listening(self) -> None:
        """Start audio capturing and begin processing here"""
        self._is_running = True
        self.capture.set_chunk_callaback(self._on_audio_callback)
        self.capture.start()
        await self.event_bus.publish("audio.listening_started", {})
        logger.info("Audio pipeline listening started")
    
    async def stop_listening(self) -> None:
        """Stop audio capturing"""
        self._is_running = False
        self.capture.stop()
        await self.event_bus.publish("audio.listening_stopped", {})
        logger.info("Audio pipeling listening stopped")

    async def get_user_utterance(self) -> str:
        pass

    async def process_utterance(self, text: str) -> Optional[str]:
        pass
    
    def _on_audio_callback(self, chunk: np.ndarray) -> None:
        """Callback func for sounddevice when new chunk arrives.
        
        Pushes chunk into a thread-safe queue so that
        get_user_utterance() can conuse exactly once
        """
        self._audio_queue.put_nowait(chunk)