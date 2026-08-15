import queue
import numpy as np
import sounddevice as sd
import soundfile as sf

# Configuration settings
SAMPLE_RATE = 16000  
CHANNELS = 1         
BLOCK_SIZE = 1024    
OUTPUT_FILENAME = "data\\hindi_5.wav"

# ⏱️ Set your desired recording duration here (in seconds)
RECORD_SECONDS = 5.0

# Calculate the precise number of blocks needed to fulfill the duration
total_blocks_to_record = int((SAMPLE_RATE * RECORD_SECONDS) / BLOCK_SIZE)

# Thread-safe queue to pass audio chunks from the callback [cite: 6]
audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    """
    Asynchronous callback that intercepts audio data from your microphone[cite: 130, 131, 423].
    """
    if status:
        print(f"Error in audio stream: {status}")
    # Put a copy of the raw numpy array into our thread queue [cite: 2, 6]
    audio_queue.put(indata.copy())

recorded_chunks = []

print(f"🎙️ Recording active... Capturing exactly {RECORD_SECONDS} seconds of audio.")

# Initialize and start the asynchronous input stream [cite: 130, 131]
with sd.InputStream(samplerate=SAMPLE_RATE, 
                    channels=CHANNELS, 
                    blocksize=BLOCK_SIZE, 
                    callback=audio_callback):
    
    # Loop exactly the number of times required for the requested duration
    for _ in range(total_blocks_to_record):
        # Fetch individual chunks sequentially as they arrive from the driver
        chunk = audio_queue.get() 
        recorded_chunks.append(chunk)

print("🛑 Time limit reached. Stream closed automatically.")

# Processing and saving the collected data [cite: 130, 131]
if recorded_chunks:
    print("💾 Saving audio file...")
    # Stack individual chunks into a single comprehensive matrix [cite: 9]
    final_audio = np.vstack(recorded_chunks)
    # Write to a standard WAV container file [cite: 3]
    sf.write("ztest\\"+OUTPUT_FILENAME, final_audio, SAMPLE_RATE)
    print(f"🎉 Successfully saved to: {OUTPUT_FILENAME}")