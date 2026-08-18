"""
MainWindow which shows desktop UI, floating window
"""

import logging

import numpy as np
from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget
)

from audio.capture import AudioCapture
from ui.bridge import PyQtEventBridge
from ui.widgets import FloatingOrb

logger = logging.getLogger(__name__)

MAIN_WINDOW_STYLE = """
QWidget#centralWidget {
    background-color: #0c0d14;
}
"""


class MainWindow(QMainWindow):
    """Main Desktop Window"""

    def __init__(
        self,
        event_bridge: PyQtEventBridge,
        audio_capture: AudioCapture,
        title: str = "S.Y.N.C."
    ) -> None:
        super().__init__()
        self.event_bridge = event_bridge
        self.audio_capture = audio_capture
        self.fft_max_val = 0.1  # For dynamic auto-gain visualizer scaling

        # timer for visualizer
        self.visualizer_timer = QTimer(self)
        self.visualizer_timer.setInterval(25)  # 25ms interval (~40 FPS) for smooth animation
        self.visualizer_timer.timeout.connect(self._update_waveform)
        self.visualizer_timer.start()  # Run continuously to keep the visualizer breathing while quiet

        self.setWindowTitle(title)  # window title
        self.resize(900, 600)
        self.setMinimumSize(800, 550)  # min size to set window
        self.setStyleSheet(MAIN_WINDOW_STYLE)  # setting custom window styling

        self.orb = FloatingOrb()  # orb widget instance

        # Core central widget
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # connect event bridge signals
        self.event_bridge.event_received.connect(self._on_event_received)

        # setting orb location and show
        main_geo = self.geometry()
        self.orb.move(main_geo.right() + 20, main_geo.top())
        self.orb.show()

    # update waveform by updating and setting audio data
    def _update_waveform(self) -> None:
        # Fetch only the last 1024 samples if capture is running
        if self.audio_capture._running:
            recent_samples = self.audio_capture.get_recent_audio(1024)
        else:
            recent_samples = None

        if recent_samples is not None and len(recent_samples) > 0:
            sample_rate = getattr(self.audio_capture, "sample_rate", 16000)
            n_samples = len(recent_samples)
            
            # Pad with zeros if n_samples < 1024 to keep consistent frequency resolution
            if n_samples < 1024:
                padded_samples = np.pad(recent_samples, (0, 1024 - n_samples), 'constant')
            else:
                padded_samples = recent_samples

            # Run FFT with Hanning window to prevent spectral leakage
            window = np.hanning(1024)
            windowed_samples = padded_samples * window
            fft_vals = np.abs(np.fft.rfft(windowed_samples))

            # Extract 16 logarithmic frequency bands from 80 Hz to 4000 Hz (speech range)
            num_bins = 16
            freqs = np.geomspace(80, 4000, num_bins + 1)
            bin_edges = (freqs * 1024 / sample_rate).astype(int)

            # Adjust edges to be unique and strictly increasing
            for i in range(1, len(bin_edges)):
                if bin_edges[i] <= bin_edges[i - 1]:
                    bin_edges[i] = bin_edges[i - 1] + 1

            bands = []
            for i in range(num_bins):
                start_idx = bin_edges[i]
                end_idx = bin_edges[i + 1]
                val = np.mean(fft_vals[start_idx:end_idx]) if start_idx < len(fft_vals) else 0.0
                bands.append(val)

            # Auto-Gain Control (AGC) for dynamic visualizer responsiveness
            bands = np.array(bands)
            current_peak = np.max(bands)
            if current_peak > self.fft_max_val:
                # Fast track upward peaks
                self.fft_max_val = self.fft_max_val * 0.2 + current_peak * 0.8
            else:
                # Faster decay downward (0.95) to adapt to quiet speech in under 1 second
                self.fft_max_val = self.fft_max_val * 0.95 + max(current_peak, 0.0001) * 0.05

            # Normalize bands dynamically using peak tracker
            if self.fft_max_val > 0.0:
                normalized_bands = np.clip(bands / self.fft_max_val, 0.0, 1.0)
            else:
                normalized_bands = np.zeros(num_bins)

            # Max-pooling extraction for highly responsive frequency-specific animations
            level = min(np.max(normalized_bands) * 1.2, 1.0)
            bass_level = min(np.max(normalized_bands[0:5]) * 1.2, 1.0)
            mid_level = min(np.max(normalized_bands[4:11]) * 1.2, 1.0)
            treble_level = min(np.max(normalized_bands[10:16]) * 1.2, 1.0)
            bands = normalized_bands
        else:
            level = 0.0
            bands = np.zeros(16)
            bass_level = 0.0
            mid_level = 0.0
            treble_level = 0.0

        self.orb.set_audio_data(level, bands, bass_level, mid_level, treble_level)

    
    @pyqtSlot(str, dict)
    def _on_event_received(self, name: str, payload: dict) -> None:
        """Signal routing logic updating UI widgets on incoming backend activity"""
        logger.debug("MainWindow received signal event: %s", name)

        if name == "audio.listening_stopped":
            # reset orb level when listening stops
            self.orb.set_audio_level(0.0)

    # clearing up
    def closeEvent(self, event):
        self.orb.close()
        event.accept()
