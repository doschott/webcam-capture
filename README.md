# webcam-capture

Capture images from a webcam via Windows DirectShow using OpenCV. Designed for WSL2 environments where USBIP isochronous transfers fail.

## Why

WSL2's USBIP driver (`vhci_hcd`) cannot handle isochronous USB transfers — the high-bandwidth, low-latency transfers webcams use for video. This produces placeholder images (~13KB with EXIF metadata, no real pixels). This skill uses Windows DirectShow via OpenCV instead.

## Setup

### Windows

```powershell
winget install Python.Python.3.12
python -m pip install opencv-python-headless
```

### Copy the capture script

```powershell
# Download wincam.py to C:\Users\Public\
```

Or copy from this repo:
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/doschott/webcam-capture/main/wincam.py" -OutFile "C:\Users\Public\wincam.py"
```

## Usage

```powershell
# Capture (runs on Windows, saves to C:\Users\Public\)
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\wincam.py'

# From WSL, copy the result:
cp /mnt/c/Users/Public/webcam_capture.jpg output.jpg
```

## How It Works

```
Windows DirectShow -> OpenCV -> C:\Users\Public\webcam_capture.jpg -> WSL -> file
```

The webcam stays accessible to Windows while WSL reads the output file via `/mnt/c/`.

## Requirements

- Windows 10/11
- Python 3.12 with OpenCV (`pip install opencv-python-headless`)
- ffmpeg (`winget install Gyan.FFmpeg`) for video recording
- Logitech Brio 100 (or any DirectShow-compatible webcam)
- WSL2 (optional, for reading output in Linux environments)

## Capture Settings

- Resolution: 640x480 (native, best quality)
- Format: Camera's native YUYV mode
- Auto-exposure: Enabled (discards first 5 frames to let exposure settle)
- Output: C:\Users\Public\webcam_capture.jpg

## Technical Notes

- **USBIP does NOT work** for webcam video in WSL2. The `vhci_hcd` kernel module drops isochronous URBs (`urb->status -104`).
- The webcam light being "on" means USB enumeration works, but actual video transfer requires isochronous transfers which fail silently over USBIP.
- Windows DirectShow has no such limitation and captures reliably.
