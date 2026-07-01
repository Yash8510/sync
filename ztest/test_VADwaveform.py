import sys
import asyncio
import threading
from collections import deque

import numpy as np
import torch

from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from sounddevice import InputStream
from silero_vad import load_silero_vad

# Silero VAD here
# -----------------------------------------------------------------------------------------------------------
model = load_silero_vad()
print("Silero VAD model loaded")

max_prob = 0

def vad(audio):
    global max_prob
    print("inside vad : ", len(audio))
    count = 0
    max_prob = 0
    for start in range(0, len(audio) - 512 + 1, 512):
        frame = audio[start : start+512]
        prob = model(torch.from_numpy(frame), 16000).item()
        print(f"{prob:.2}")
        if prob > max_prob:
            max_prob = prob
        count += 1
    print("count: ", count)
    print("\n")

async def run_vad():
    with lock:
        if len(buffer) > 0:
            buffer_list = np.concatenate(list(buffer))
        else:
            return
    try:
        vad(buffer_list)
    except Exception as e:
        print(e)

# -----------------------------------------------------------------------------------------------------------


# async running loop here & app instance created & asyncio event loop instanced
# -----------------------------------------------------------------------------------------------------------
shutdown_event = threading.Event()

async def run() -> None:
    stream.start()
    while not shutdown_event.is_set():
        await run_vad()
        await asyncio.sleep(1)
    stream.stop()
    print("stream stopped")


def start_async_loop(loop) -> None:
    print("async loop entered")
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())
    print("complete")

app = QApplication(sys.argv)

loop = asyncio.new_event_loop()
# -----------------------------------------------------------------------------------------------------------


# buffer & InputStream instance & callback
# -----------------------------------------------------------------------------------------------------------
lock = threading.Lock()
buffer = deque(maxlen=(16000 * 5) // 4096)

def _audio_callback(indata: np.ndarray, frames: int, time_info, status):
    chunk = indata[:, 0].astype(np.float32).copy()
    with lock:
        buffer.append(chunk)

stream = InputStream(
    samplerate=16000,
    channels=1,
    blocksize=1024,
    callback=_audio_callback,
    latency=0.1
)
# -----------------------------------------------------------------------------------------------------------


# PyQt6 window instance & show
# -----------------------------------------------------------------------------------------------------------

class AudioVisualizerWidget(QWidget):
    def __init__(self, buffer, lock):
        super().__init__()
        self.buffer = buffer
        self.lock = lock
        self.waveform = np.array([], dtype=np.float32)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))  # Black background
        
        # Get audio data safely
        with self.lock:
            if len(self.buffer) > 0:
                self.waveform = np.concatenate(list(self.buffer))
        
        # Draw waveform
        if len(self.waveform) > 0:
            width = self.width()
            height = self.height()
            
            if max_prob > 0.5:
                painter.setPen(QPen(QColor(0, 255, 0), 1))  # Green line
            else:
                painter.setPen(QPen(QColor(0, 0, 255), 1))  # blue color
            
            # Downsample waveform to fit screen
            step = max(1, len(self.waveform) // width)
            x_points = np.arange(0, len(self.waveform), step)
            y_points = (self.waveform[::step] * height / 2 + height / 2).astype(int)
            
            for i in range(len(x_points) - 1):
                painter.drawLine(
                    int(x_points[i] * width / len(self.waveform)),
                    int(y_points[i]),
                    int(x_points[i+1] * width / len(self.waveform)),
                    int(y_points[i+1])
                )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Visualize")
        self.resize(800, 400)

        self.visualizer = AudioVisualizerWidget(buffer, lock)
        self.setCentralWidget(self.visualizer)

        self.timer = QTimer()
        self.timer.timeout.connect(self.visualizer.update)
        self.timer.start(20)
    
    def closeEvent(self, a0):
        self.timer.stop()
        shutdown_event.set()
        a0.accept()

window = MainWindow()
window.show()
# -----------------------------------------------------------------------------------------------------------


# thread instance & start thread & exec app
# -----------------------------------------------------------------------------------------------------------
print("starting thread")
thread = threading.Thread(
    target=start_async_loop,
    args=(loop,),
    daemon=True
)
thread.start()
exit_code = app.exec()
# -----------------------------------------------------------------------------------------------------------


print("end")
