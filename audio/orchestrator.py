"""
main file which manages audio capture, VAD, STT, TTS, intent routing, playback
into a single file
"""

import logging
import asyncio
from typing import Dict, Optional

import numpy as np
import queue as _queue

from audio.capture import AudioCapture
from audio.turn_taking import TurnTaker
from audio.vad import VADDectector
from core.event_bus import EventBus
from speech.stt import STTEngine

logger = logging.getLogger(__name__)


class AudioSpeechPipeline:
    """orchestrate audio capture, VAD, STT, TTS, intent routing, playback"""
    def __init__(
        self,
        event_bus: EventBus,
        speech_cfg: Dict
    ):
        self.sample_rate = speech_cfg.get("sample_rate")
        self.event_bus = event_bus
        self.capture = AudioCapture(sample_rate=self.sample_rate,
                                    chunk_size=speech_cfg.get("chunk_size"),
                                    buffer_seconds=speech_cfg.get("buffer_seconds"))
        self.vad = VADDectector(sample_rate=self.sample_rate)
        self.turn_taker = TurnTaker(
            silence_threshold=speech_cfg.get("silence_threshold", 1.5),
            sample_rate=self.sample_rate,
            vad_detector=self.vad
        )
        self.stt = STTEngine(model_size=speech_cfg["stt_model"]["distil-large-v3.5"], device="cuda", compute_type="float32")
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
        """Wait for user to speak and return transcribed text.
        
        Uses an internal thread-safe queue so that sounddevice
        callback chunks exactly once and then consumer drains them cleanly.
        """
        logger.debug("waiting for user utterance...")
        await self.event_bus.publish("audio.awaiting_speech", {})

        # reset speech state each time
        self.turn_taker.reset()

        # drain out stale chunks of audio from previous turn
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except _queue.Empty:
                break
        
        accumulated_audio: list[np.ndarray] = []

        async def wait_for_speech() -> None:
            # Phase-1: wait until VAD detect speech
            while self._is_running and not self.turn_taker._user_is_speaking:
                # pull out audio chunk from queue
                try:
                    chunk = self._audio_queue.get_nowait()  # get audio from queue
                    self.turn_taker.update(chunk)  # process audio chunk & update speech state
                except _queue.Empty:
                    pass
                await asyncio.sleep(0.05)
            
            # Phase-2: collect audio while user is still speaking
            while self._is_running and not self.turn_taker.is_done_speaking():
                try:
                    chunk = self._audio_queue.get_nowait()
                    self.turn_taker.update(chunk)
                    accumulated_audio.append(chunk)
                except _queue.Empty:
                    pass
                await asyncio.sleep(0.05)
            
            # remove remaining audio chunk from queue after silence is detected
            while not self._audio_queue.empty():
                try:
                    self._audio_queue.get_nowait()
                except _queue.Empty:
                    break

        try:
            print("waiting for speech")
            await asyncio.wait_for(wait_for_speech(), timeout=30.0)  # wait for speech for 30s
        except asyncio.TimeoutError:
            logger.warning("User utterance timeout")
            return ""
        except Exception as e:
            logger.exception("Error waiting for speech: %s", e)
            return ""
        
        # if no speech detected then return empty str
        if not accumulated_audio:
            return ""
        
        combined_audio = np.concatenate(accumulated_audio)  # accumulate audio for speech transcription
        if len(combined_audio) > 0:
            # transcript audio to txt here
            print("speech detected & transcriptions in here")
            text, _, _ = self.stt.transcribe(combined_audio)
            return text
        else:
            return ""


    async def process_utterance(self, text: str) -> Optional[str]:
        print(text)
    
    def _on_audio_callback(self, chunk: np.ndarray) -> None:
        """Callback func for sounddevice when new chunk arrives.
        
        Pushes chunk into a thread-safe queue so that
        get_user_utterance() can conuse exactly once
        """
        self._audio_queue.put_nowait(chunk)