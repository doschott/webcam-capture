# webcam-capture

Capture images, audio, and video from a webcam via Windows native APIs. Includes wake word listener for voice-activated photo capture. Designed for WSL2 environments where USBIP isochronous transfers fail.

## Features

| Mode | Script | Output | Format |
|------|--------|--------|--------|
| **Image** | `wincam.py` | Snapshot | JPEG 640x480 |
| **Audio** | `win_audio.py` | Recording | WAV 44.1kHz PCM mono |
| **Video** | `win_video.py` | Recording | MP4 H.264 + AAC |
| **Wake Word** | `win_wake.py` | Voice control | Listens for "DOSBot" |

## Wake Word Listener

Run `win_wake.py` and say "DOSBot" to trigger a photo capture automatically:
- Uses Google Speech Recognition for STT (requires internet)
- Energy-based speech detection
- Minimal storage (only saves audio when speech detected)
- Action log at `C:\Users\Public\wake_log.txt`

## Why This Approach

WSL2's USBIP driver (`vhci_hcd`) cannot handle isochronous USB transfers — the high-bandwidth, low-latency transfers webcams use for video and audio. USBIP produces placeholder images (~13KB with EXIF metadata, no real pixels). This skill uses Windows native APIs instead:

- **Video/Audio**: DirectShow via ffmpeg
- **Image**: DirectShow via OpenCV
- **Audio only**: WASAPI via PyAudio

## Setup

### Windows

```powershell
winget install Python.Python.3.12
python -m pip install opencv-python-headless pyaudio speech_recognition
winget install Gyan.FFmpeg

# Create folder structure:
New-Item -ItemType Directory -Path 'C:\Users\Public\claw-webcam-capture\image' -Force
New-Item -ItemType Directory -Path 'C:\Users\Public\claw-webcam-capture\audio' -Force
New-Item -ItemType Directory -Path 'C:\Users\Public\claw-webcam-capture\video' -Force
New-Item -ItemType Directory -Path 'C:\Users\Public\claw-webcam-capture\listener-jarvis' -Force
```

### Copy the scripts

```bash
cp webcam-capture/wincam.py /mnt/c/Users/Public/claw-webcam-capture/image/wincam.py
cp webcam-capture/win_audio.py /mnt/c/Users/Public/claw-webcam-capture/audio/win_audio.py
cp webcam-capture/win_video.py /mnt/c/Users/Public/claw-webcam-capture/video/win_video.py
cp webcam-capture/win_wake.py /mnt/c/Users/Public/claw-webcam-capture/listener-jarvis/win_wake.py
```

## Usage

```powershell
# Image capture
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\claw-webcam-capture\image\wincam.py'

# Audio recording (5 seconds)
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\claw-webcam-capture\audio\win_audio.py'

# Video recording with audio (5 seconds, or pass duration as arg)
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\claw-webcam-capture\video\win_video.py' 10

# Wake word listener
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\claw-webcam-capture\listener-jarvis\win_wake.py'

# From WSL, copy results:
cp /mnt/c/Users/Public/claw-webcam-capture/image/webcam_capture.jpg output.jpg
cp /mnt/c/Users/Public/claw-webcam-capture/audio/audio_capture.wav output.wav
cp /mnt/c/Users/Public/claw-webcam-capture/video/video.mp4 output.mp4
```

## Technical Details

- **Image**: 640x480 JPEG, native YUYV mode (not forced MJPG), 5-frame warmup for auto-exposure
- **Audio**: Brio 100 mic as "Microphone (Brio 100)", 44.1kHz mono 16-bit PCM, ~88KB/s
- **Video**: ffmpeg DirectShow, H.264 video + AAC audio, ~370KB/s
- **Devices**: Uses Brio 100 webcam + built-in mic via DirectShow/WASAPI

## Requirements

- Windows 10/11
- Python 3.12 with OpenCV, PyAudio, and SpeechRecognition
- ffmpeg (Gyan.FFmpeg) for video recording
- Logitech Brio 100 (or any DirectShow-compatible webcam/mic)
