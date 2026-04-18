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

WAKE_WORD = "dosbot"
ENERGY_THRESHOLD = 300
SILENCE_FRAMES = 10
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

BASE = r"C:\Users\Public\claw-webcam-capture"
IMAGE_DIR = BASE + r"\image"
AUDIO_DIR = BASE + r"\listener-jarvis"
PYTHON = r"C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe"
WINCAM = r"C:\Users\Public\claw-webcam-capture\wincam.py"
AUDIO_BUFFER = AUDIO_DIR + r"\wake_audio.wav"
LOG_FILE = AUDIO_DIR + r"\wake_log.txt"

audio_buffer = []
in_speech = False
silence_count = 0
buffer_lock = threading.Lock()
recognizer = sr.Recognizer()
recognizer.energy_threshold = ENERGY_THRESHOLD


def find_brio_mic(p):
    for i in range(p.get_device_count()):
        d = p.get_device_info_by_index(i)
        if d['maxInputChannels'] > 0 and 'Brio' in d.get('name', ''):
            return i
    return None


def transcribe(audio_path):
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio).lower()
        print("  Heard: %s" % text)
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print("  STT error: %s" % e)
        return None


def trigger_action():
    print("  WAKE WORD DETECTED! Taking photo...")
    try:
        # Update WINCAM path to new location
        import shutil
        shutil.copy(WINCAM, IMAGE_DIR + r"\wincam.py")
        subprocess.run([PYTHON, IMAGE_DIR + r"\wincam.py"], check=True)
        print("  Photo captured!")
        with open(LOG_FILE, "a") as f:
            f.write("%s - WAKE: photo taken\n" % time.strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        print("  Action error: %s" % e)


def process_buffer(buf):
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
    print("Wake word: '%s'" % WAKE_WORD)
    print("=" * 50)

    p = pyaudio.PyAudio()
    brio_idx = find_brio_mic(p)
    if brio_idx is None:
        print("ERROR: Brio 100 mic not found")
        p.terminate()
        sys.exit(1)

    print("Using device %d: Microphone (Brio 100)" % brio_idx)

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
