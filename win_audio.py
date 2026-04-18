import pyaudio, wave, sys, os, time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
OUTPUT = r"C:\Users\Public\claw-webcam-capture\audio\audio_capture.wav"

p = pyaudio.PyAudio()
brio_idx = None
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d['maxInputChannels'] > 0 and 'Brio' in d['name'] and brio_idx is None:
        brio_idx = i
        print("Using: device %d: %s" % (i, d['name']))

if brio_idx is None:
    print("ERROR: Brio 100 mic not found")
    p.terminate()
    sys.exit(1)

stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                 input=True, input_device_index=brio_idx,
                 frames_per_buffer=CHUNK)

print("Recording %ds..." % RECORD_SECONDS)
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
print("OK: %s (%d bytes, %ds)" % (OUTPUT, size, RECORD_SECONDS))
