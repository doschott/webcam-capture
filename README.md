# webcam-capture

Capture images, audio, and video from a webcam via Windows native APIs. Designed for WSL2 environments where USBIP isochronous transfers fail.

## Features

| Mode | Script | Output | Format |
|------|--------|--------|--------|
| **Image** | `wincam.py` | Snapshot | JPEG 640x480 |
| **Audio** | `win_audio.py` | Recording | WAV 44.1kHz PCM mono |
| **Video** | `win_video.py` | Recording | MP4 H.264 + AAC |

## Why This Approach

WSL2's USBIP driver (`vhci_hcd`) cannot handle isochronous USB transfers — the high-bandwidth, low-latency transfers webcams use for video and audio. USBIP produces placeholder images (~13KB with EXIF metadata, no real pixels). This skill uses Windows native APIs instead:

- **Video/Audio**: DirectShow via ffmpeg
- **Image**: DirectShow via OpenCV
- **Audio only**: WASAPI via PyAudio

## Setup

### Windows

```powershell
winget install Python.Python.3.12
python -m pip install opencv-python-headless pyaudio
winget install Gyan.FFmpeg
```

### Copy the scripts

```powershell
# From WSL:
cp webcam-capture/wincam.py /mnt/c/Users/Public/wincam.py
cp webcam-capture/win_audio.py /mnt/c/Users/Public/win_audio.py
cp webcam-capture/win_video.py /mnt/c/Users/Public/win_video.py
```

## Usage

```powershell
# Image capture
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\wincam.py'

# Audio recording (5 seconds)
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\win_audio.py'

# Video recording with audio (5 seconds, or pass duration as arg)
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\win_video.py' 10

# From WSL, copy results:
cp /mnt/c/Users/Public/webcam_capture.jpg output.jpg
cp /mnt/c/Users/Public/audio_capture.wav output.wav
cp /mnt/c/Users/Public/video.mp4 output.mp4
```

## Technical Details

- **Image**: 640x480 JPEG, native YUYV mode (not forced MJPG), 5-frame warmup for auto-exposure
- **Audio**: Brio 100 mic as "Microphone (Brio 100)", 44.1kHz mono 16-bit PCM, ~88KB/s
- **Video**: ffmpeg DirectShow, H.264 video + AAC audio, ~370KB/s
- **Devices**: Uses Brio 100 webcam + built-in mic via DirectShow/WASAPI

## Requirements

- Windows 10/11
- Python 3.12 with OpenCV and PyAudio
- ffmpeg (Gyan.FFmpeg) for video recording
- Logitech Brio 100 (or any DirectShow-compatible webcam/mic)
