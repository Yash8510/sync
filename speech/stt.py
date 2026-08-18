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
        """Load faster whisper model with automatic local cache resolution"""
        from pathlib import Path
        
        target_model = self.model_size
        project_root = Path(__file__).resolve().parent.parent
        stt_dir = project_root / "models" / "stt"

        # 1. Check if model_size is a direct existing directory path
        direct_path = Path(self.model_size)
        if not direct_path.is_absolute():
            direct_path = project_root / direct_path
        
        if direct_path.exists() and direct_path.is_dir():
            target_model = str(direct_path)
        elif stt_dir.exists():
            # 2. Check for matching local snapshot directory under models/stt/
            model_key = self.model_size.split("/")[-1]
            matches = list(stt_dir.glob(f"*{model_key}*/**/model.bin"))
            if not matches:
                # Fallback search by base name
                base_name = model_key.replace("faster-whisper-", "").replace("distil-", "")
                matches = list(stt_dir.glob(f"*{base_name}*/**/model.bin"))
            
            if matches:
                target_model = str(matches[0].parent)

        local_only = Path(target_model).exists()
        try:
            self.model = WhisperModel(
                target_model,
                device=self.device,
                compute_type=self.compute_type,
                local_files_only=local_only
            )
            logger.info("Faster Whisper model (%s) loaded on device: (%s) with: (%s) [local_files_only=%s]", target_model, self.device, self.compute_type, local_only)
        except Exception as e:
            logger.error("Failed to load Whisper model from %s: %s", target_model, e)

    def transcribe(self, audio: np.ndarray):
        """Transcribe audio to text.
        
        Args:
            audio: audio array, mono
        
        Returns:
            Transcribed text, segments, info
        """
        if self.model is None:
            logger.error("Faster whisper model not loaded")
            return "", None, None
        
        segments, info = None, None
        try:
            segments, info = self.model.transcribe(audio=audio, vad_filter=True)
            text = " ".join([segment.text for segment in segments])
            return text, segments, info
        except Exception as e:
            logger.exception("STT Transcription error: %s", e)
            return "", None, None
