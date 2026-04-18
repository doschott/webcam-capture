import pyaudio, wave, sys, os

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
OUTPUT = r"C:\Users\Public\audio_capture.wav"

p = pyaudio.PyAudio()

# Find Brio 100 mic
brio_idx = None
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d['maxInputChannels'] > 0 and 'Brio' in d['name']:
        print(f"Found: device {i}: {d['name']} ({d['maxInputChannels']}ch, {d['defaultSampleRate']}Hz)")
        if brio_idx is None:
            brio_idx = i

if brio_idx is None:
    print("ERROR: Brio 100 mic not found")
    p.terminate()
    sys.exit(1)

stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                 input=True, input_device_index=brio_idx,
                 frames_per_buffer=CHUNK)

print(f"Recording {RECORD_SECONDS} seconds...")
frames = []
for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    frames.append(data)

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(OUTPUT, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

size = os.path.getsize(OUTPUT)
print(f"OK: {OUTPUT} ({size} bytes, {RECORD_SECONDS}s)")
