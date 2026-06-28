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

# class ListeningOrbWindow(QWidget):
#     """A Floating Orb"""

#     def __init__(self):
#         super().__init__()

#         self.setFixedSize(100, 100)

#         self.setWindowFlags(
#             Qt.WindowType.FramelessWindowHint |
#             Qt.WindowType.WindowStaysOnTopHint |
#             Qt.WindowType.Tool
#         )

#         self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

#         self.drag_position = QPoint()

#         img_path = Path(__file__).resolve().parent / "images" / "wave-sound.png"

#         self.img = QLabel(self)
#         self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.img.setPixmap(QPixmap(str(img_path)))
#         self.img.setScaledContents(True)

#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(self.img)

#     def mousePressEvent(self, event):
#         if event.button() == Qt.MouseButton.LeftButton:
#             self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
#             event.accept()

#     def mouseMoveEvent(self, event):
#         if event.buttons() & Qt.MouseButton.LeftButton:
#             self.move(event.globalPosition().toPoint() - self.drag_position)
#             event.accept()


class MainWindow(QMainWindow):
    """Main Desktop Window"""

    def __init__(
        self,
        event_bridge: PyQtEventBridge,
        audio_capture: AudioCapture
    ) -> None:
        super().__init__()
        self.event_bridge = event_bridge
        self.audio_capture = audio_capture

        # timer for visualizer
        self.visualizer_timer = QTimer(self)
        self.visualizer_timer.setInterval(16)  # 16 -> 60 FPS, 33 -> 30 FPS
        self.visualizer_timer.timeout.connect(self._update_waveform)

        self.setWindowTitle("Assistant")  # window title
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
        audio_data = self.audio_capture.get_buffered_audio()

        if audio_data is not None and len(audio_data) > 0:
            # Get the most recent 1024 samples (approx. 64ms at 16kHz) for responsive peak detection
            recent_samples = audio_data[-min(len(audio_data), 1024):]
            
            # Root Mean Square (RMS) calculation
            rms = np.sqrt(np.mean(recent_samples ** 2))
            
            # Scale the RMS value so standard speech reaches high levels (up to 1.0)
            level = min(rms * 8.0, 1.0)
        else:
            level = 0.0

        self.orb.set_audio_level(level)

    
    @pyqtSlot(str, dict)
    def _on_event_received(self, name: str, payload: dict) -> None:
        """Signal routing logic updating UI widgets on incoming backend activity"""
        logger.debug("MainWindow received signal event: %s", name)

        if name == "audio.listening_started":
            # start visualizer timer
            self.visualizer_timer.start()

        elif name == "audio.listening_stopped":
            # stop visualizer timer and reset orb level
            self.visualizer_timer.stop()
            self.orb.set_audio_level(0.0)

    # clearing up
    def closeEvent(self, event):
        self.orb.close()
        event.accept()
