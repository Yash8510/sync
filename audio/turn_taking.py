"""Turn taking controller (user speech & replying)"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from audio.vad import VADDectector

logger = logging.getLogger(__name__)


class TurnTaker:
    """Manages conversation turns"""

    def __init__(self, silence_threshold: float, sample_rate: int, vad_detector: VADDectector):
        self.silence_threshold = timedelta(seconds=silence_threshold)
        self.vad = vad_detector or VADDectector(sample_rate=sample_rate)
        self._last_speech_time: Optional[datetime] = None
        self._user_is_speaking = False

    def update(self, audio_chunk: np.ndarray) -> None:
        """Process audio chunk and update speech state"""

        is_speech, confidence = self.vad.detect(audio=audio_chunk)

        if is_speech and confidence > 0.5:  # confidence >0.5
            self._last_speech_time = datetime.now()
            self._user_is_speaking = True
        else:
            if self._last_speech_time and datetime.now() - self._last_speech_time > self.silence_threshold:  # silence threshold check
                self._user_is_speaking = False

    def is_speaking(self):
        """Is user currently speaking ?"""
        return self._user_is_speaking
    
    def is_done_speaking(self):
        """Is user done speaking & is silence detected ?"""
        if not self._last_speech_time:
            return False
        return datetime.now() - self._last_speech_time > self.silence_threshold  # silence threshold check

    def reset(self) -> None:
        """Reset turn state"""
        self._last_speech_time = None
        self._user_is_speaking = False
