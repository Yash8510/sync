"""
Microphone capture with ring buffer to handle continuous audio capturing
"""

import threading
import logging
from collections import deque
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioCapture:
    """Realtime audio capturing"""
    def __init__(
        self,
        sample_rate: int,
        chunk_size: int,
        buffer_seconds: int
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.buffer_seconds = buffer_seconds
        self.buffer = deque(maxlen=(sample_rate * buffer_seconds) // chunk_size)
        self._lock = threading.Lock()
        self._stream: Optional[sd.InputStream] = None
        self._running = False
        self._on_chunk: Optional[Callable[[np.ndarray], None]] = None

    def set_chunk_callaback(self, callback: Callable[[np.ndarray], None]) -> None:
        """Register callback to be invoked when each chunk is captured """
        self._on_chunk = callback
    
    def start(self) -> None:
        """Start capturing audio in background thread"""

        if self._running:
            return
        
        self._running = True

        def audio_callback(indata: np.ndarray, frames: int, time_info, status) -> None:
            if status:
                logger.warning("Audio capture status: %s", status)
            chunk = indata[:, 0].astype(np.float32).copy()
            with self._lock:
                self.buffer.append(chunk)
            if self._on_chunk:
                self._on_chunk(chunk)
        
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                blocksize=self.chunk_size,
                callback=audio_callback,
                latency=0.1
            )
            self._stream.start()
            logger.info("Audio capture started")
        except Exception as e:
            logger.error("Failed to start audio capture: %s", e)
            self._running = False
    
    def stop(self) -> None:
        """Stop capturing audio"""

        if not self._running:
            return
        
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Audio capture stopped")

    def get_recent_audio(self, num_samples: int) -> np.ndarray:
        """Return the most recent `num_samples` audio samples efficiently without concatenating the whole buffer"""
        with self._lock:
            if not self.buffer:
                return np.empty(0, dtype=np.float32)
            
            chunks_needed = []
            samples_accumulated = 0
            
            # Traverse the deque backwards to gather just enough chunks
            for chunk in reversed(self.buffer):
                chunks_needed.append(chunk)
                samples_accumulated += len(chunk)
                if samples_accumulated >= num_samples:
                    break
            
            # Restore chronological order
            chunks_needed.reverse()
            
            if not chunks_needed:
                return np.empty(0, dtype=np.float32)
                
            concatenated = np.concatenate(chunks_needed)
            return concatenated[-num_samples:]
