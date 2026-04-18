"""
Wake Word Listener for DOSBot
Streams audio from Brio 100 mic, detects speech, transcribes with Google Speech Recognition,
and triggers photo capture when "DOSBot" is heard.
"""
import pyaudio
import wave
import os
import sys
import threading
import time
import subprocess
import speech_recognition as sr

# Config
WAKE_WORD = "dosbot"
ENERGY_THRESHOLD = 300  # Adjust based on ambient noise
SILENCE_FRAMES = 10  # Frames of silence to end a phrase
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Paths
PYTHON = r"C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe"
WINCAM = r"C:\Users\Public\wincam.py"
AUDIO_BUFFER = r"C:\Users\Public\wake_audio.wav"
LOG_FILE = r"C:\Users\Public\wake_log.txt"

audio_buffer = []
in_speech = False
silence_count = 0
buffer_lock = threading.Lock()
recognizer = sr.Recognizer()
recognizer.energy_threshold = ENERGY_THRESHOLD


def find_brio_mic(p):
    """Find Brio 100 mic device index."""
    for i in range(p.get_device_count()):
        d = p.get_device_info_by_index(i)
        if d['maxInputChannels'] > 0 and 'Brio' in d.get('name', ''):
            return i
    return None


def transcribe(audio_path):
    """Transcribe audio file using Google Speech Recognition."""
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio).lower()
        print(f"  Heard: {text}")
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"  STT error: {e}")
        return None


def trigger_action():
    """Take a photo when wake word detected."""
    print("  WAKE WORD DETECTED! Taking photo...")
    try:
        subprocess.run([PYTHON, WINCAM], check=True)
        print("  Photo captured!")
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - WAKE: photo taken\n")
    except Exception as e:
        print(f"  Action error: {e}")


def process_buffer(buf):
    """Process a speech buffer in a thread."""
    wf = wave.open(AUDIO_BUFFER, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(2)
    wf.setframerate(RATE)
    wf.writeframes(b''.join(buf))
    wf.close()
    text = transcribe(AUDIO_BUFFER)
    if text and WAKE_WORD in text:
        trigger_action()


def audio_callback(in_data, frame_count, time_info, status):
    """Process audio chunks."""
    global in_speech, silence_count

    import numpy as np
    audio_data = np.frombuffer(in_data, dtype=np.int16)
    energy = np.abs(audio_data).mean()

    with buffer_lock:
        if energy > ENERGY_THRESHOLD:
            in_speech = True
            silence_count = 0
            audio_buffer.append(in_data)
        elif in_speech:
            silence_count += 1
            if silence_count >= SILENCE_FRAMES:
                in_speech = False
                silence_count = 0
                if len(audio_buffer) > 5:
                    buf_copy = list(audio_buffer)
                    audio_buffer.clear()
                    t = threading.Thread(target=lambda: process_buffer(buf_copy))
                    t.start()
            else:
                audio_buffer.append(in_data)

    return (in_data, pyaudio.paContinue)


def main():
    print("=" * 50)
    print("DOSBot Wake Word Listener")
    print(f"Wake word: '{WAKE_WORD}'")
    print(f"Energy threshold: {ENERGY_THRESHOLD}")
    print("=" * 50)

    p = pyaudio.PyAudio()

    brio_idx = find_brio_mic(p)
    if brio_idx is None:
        print("ERROR: Brio 100 mic not found")
        p.terminate()
        sys.exit(1)

    print(f"Using device {brio_idx}: Microphone (Brio 100)")

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=brio_idx,
        frames_per_buffer=CHUNK_SIZE,
        stream_callback=audio_callback
    )

    print("Listening... (Ctrl+C to stop)")
    print("Say 'DOSBot' to trigger photo capture")

    stream.start_stream()

    try:
        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")

    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Done.")


if __name__ == "__main__":
    main()
