"""Speech-to-Text managing engine"""

import logging

import pandas as pd
import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class STTEngine:
    """Speech-to-Text using:-
    > Faster Whisper"""

    def __init__(self, model_size: str, device: str = "auto", compute_type: str = "float32"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._load_model()  # load model here
    
    def _load_model(self):
        """Load faster whisper model"""
        try:
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info("Faster Whisper model (%s) loaded on device: (%s) with: (%s)", self.model_size, self.device, self.compute_type)
        except Exception as e:
            logger.error("Failed to load Whisper model: %s", e)

    def transcribe(self, audio: np.ndarray):
        """Transcribe audio to text.
        
        Args:
            audio: audio array, mono
            sample_rate: audio sample rate
        
        Returns:
            Transcribed text, segments, info
        """
        if self.model is None:
            logger.error("Faster whisper model not loaded")
            return "", None, None
        
        segments, info = None, None
        try:
            segments, info = self.model.transcribe(audio=audio, vad_filter="True")
            text = " ".join([segment.text for segment in segments])
            return text, segments, info
        except Exception as e:
            print(e)
            return "", None, None
