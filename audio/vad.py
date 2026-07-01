"""VAD: Voice Activity Detecting using Selero VAD"""

import logging

import numpy as np
from silero_vad import load_silero_vad

logger = logging.getLogger(__name__)


class VADDectector:
    """Voice Activity Dectecting wrapping Selero VAD.
    
    Selero VAD accepts *exactly* 512 samples at 16kHz (or 256 samples at 8kHz).
    This class handles audio input by windowing into 512-sample frames and
    and returns *maximum* speech probability across all frames in the chunk
    """

    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        self._frame_size = 512 if sample_rate == 16000 else 256
        self.model = None
        self.load_silero_vad_model()

    def detect(self, audio: np.ndarray) -> tuple[bool, float]:
        """Detect is audio contains speech.
        
        Accepts *any* length of audio chunks. Internally windows the audio
        chunk into 512-sample frames and returns maximum speech probability
        found across all frames.

        Args:
            audio: Audio chunk as float32 ndarray, must be 16kHz mono.

        Returns:
            ()
        """
        if self.model is None:
            return False, 0.0
        
        if len(audio) < self._frame_size:
            return False, 0.0
        
        try: 
            import torch  # already imported in main.py

            max_prob = 0.0
            # slicind window of exactly '_frame_size' samples across the chunk
            for start in range(0, len(audio) - self._frame_size + 1, self._frame_size):
                frame = audio[start : start + self._frame_size]
                prob = self.model(torch.from_numpy(frame).float(), self._frame_size).item()
                if prob > max_prob:
                    max_prob = prob
            
            is_speech = max_prob > 0.5
            return is_speech, max_prob
        except Exception as e:
            logger.error("VAD Detection error: %s", e)
            return False, 0.0
        
    def load_silero_vad_model(self):
        try:
            self.model = load_silero_vad()
            logger.info("Silero VAD model loaded (frame_size=%d)", self._frame_size)
        
        except Exception as e:
            logger.error("Failed to load Silero VAD model: %s", e)
            self.model = None
