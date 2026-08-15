import asyncio
import queue as _queue
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import wave

from audio.vad import VADDectector
from audio.turn_taking import TurnTaker
from speech.stt import STTEngine

sample_rate = 16000
chunk_size = 1024
models = {
    "tiny": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--Systran--faster-whisper-tiny\\snapshots\\d90ca5fe260221311c53c58e660288d3deb8d356\\",
    "tiny-en": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--Systran--faster-whisper-tiny.en\\snapshots\\0d3d19a32d3338f10357c0889762bd8d64bbdeba\\",
    "small": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--Systran--faster-whisper-small\\snapshots\\536b0662742c02347bc0e980a01041f333bce120\\",
    "small-en": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--Systran--faster-whisper-small.en\\snapshots\\d1d751a5f8271d482d14ca55d9e2deeebbae577f\\",
    "base-en": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--Systran--faster-whisper-base.en\\snapshots\\3d3d5dee26484f91867d81cb899cfcf72b96be6c\\",
    "base": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--Systran--faster-whisper-base\\snapshots\\ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66\\",
    "large-v3-turbo": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--mobiuslabsgmbh--faster-whisper-large-v3-turbo\\snapshots\\0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf\\",
    "distil-large-v3.5": "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\models\\stt\\models--distil-whisper--distil-large-v3.5-ct2\\snapshots\\9793ccc07920e0f830e1dba0343efcdf0ef8c903\\"
}
model_path = models["tiny"]
audio_path = "C:\\Users\\Yash\\Personal_space\\Projects\\TimePass\\assistant_bymyself\\ztest\\data\\test01_20s.wav"
vad = VADDectector(sample_rate=sample_rate)
turn_taker = TurnTaker(silence_threshold=1.5, sample_rate=sample_rate, vad_detector=vad)
stt_engine = STTEngine(model_size=model_path, device="cuda")
audio_queue = _queue.Queue()
_is_running = True

audio_array = None

print("========================================================================================")
with wave.open(audio_path, "rb") as wav_file:
    channels = wav_file.getnchannels()
    sample_width = wav_file.getsampwidth()
    sample_rate = wav_file.getframerate()
    total_frames = wav_file.getnframes()

    raw_audio = wav_file.readframes(total_frames)

    print("channels: ", channels)
    print("sample rate: ", sample_rate)
    print("total frames: ", total_frames)

    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        dtype = np.uint8
    
    audio_array = np.frombuffer(raw_audio, dtype=dtype)

# Convert int16 range to float32 between -1.0 and 1.0 (matching sounddevice capturing)
if dtype == np.int16:
    audio_array = audio_array.astype(np.float32) / 32768.0

# Group samples into chunks of 1024 before placing them in the queue
for start in range(0, len(audio_array), chunk_size):
    chunk = audio_array[start : start + chunk_size]
    if len(chunk) == chunk_size:
        audio_queue.put(chunk)

print("audio queue size: ", audio_queue.qsize())
print("========================================================================================")

# ============================
turn_taker.reset()

accumulated_audio = []

def get_user_utterance():
        
    async def wait_for_speech():
        # Phase-1 wait until VAD detect audio
        while _is_running and not turn_taker._user_is_speaking:
            try:
                chunk = audio_queue.get_nowait()
                turn_taker.update(chunk)
            except _queue.Empty:
                break
            await asyncio.sleep(0.01)
        
        # Phase-2 collect speech & detect silence
        while _is_running and not turn_taker.is_done_speaking():
            try:
                chunk = audio_queue.get_nowait()
                turn_taker.update(chunk)
                accumulated_audio.append(chunk)
            except _queue.Empty:
                break
            await asyncio.sleep(0.01)
        
        # remove remaining audio after detecting silence
        while not audio_queue.empty():
            try:
                audio_queue.get_nowait()
            except _queue.Empty:
                break

    try:
        asyncio.run(wait_for_speech())
    except Exception as e:
        print("Exception here:", e)

    segments, info = None, None
    if accumulated_audio:
        combined_audio = np.concatenate(accumulated_audio)
        if len(combined_audio) > 0:
            print("combined audio (len): ", len(combined_audio))
            print(f"Recorded duration: {len(combined_audio) / sample_rate:.2f} seconds")
            text, segments, info = stt_engine.transcribe(combined_audio)
            
            # info about audio to text
            info_data = {"lang detected: ": info.language,
                         "lang prob: ": info.language_probability,
                        "duration: ": info.duration,
                        "duration after VAD: ": info.duration_after_vad
            }
            info_data_sr = pd.Series(data=info_data)
            print(info_data_sr)
            # all lang prob
            all_lang_prob = {}
            for t in info.all_language_probs:
                all_lang_prob[t[0]] = t[1]
            
            all_lang_prob_sr = pd.Series(data=all_lang_prob)

            print("Text: ", text)

            # visualize
            plt.figure(figsize=(6, 4))
            plt.bar(all_lang_prob_sr.head().index, all_lang_prob_sr.head().values)
            plt.show()
    else:
        print("No audio accumulated.")


get_user_utterance()
