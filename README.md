# Webcam Capture for WSL2 + USBIP

Capture images, video, and audio from a webcam attached to Windows, accessed from WSL2 via USBIP.

## Setup

### 1. Windows side
```powershell
winget install usbipd
# Reboot Windows
```

### 2. WSL side (already done)
```bash
sudo apt update && sudo apt install ustreamer gstreamer1.0-plugins-good
```

### 3. Attach webcam
```powershell
# Find your webcam busid
usbipd list

# Attach
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

## Usage

```bash
cd /home/dosubuntu/clawd/projects/webcam-capture

# Check status
python3 webcam_capture.py --status

# Start streaming
python3 webcam_capture.py --start

# Capture a photo
python3 webcam_capture.py --capture /tmp/photo.jpg

# Watch mode (5 fps)
python3 webcam_capture.py --watch --fps 5

# Attach webcam (if not already attached)
python3 webcam_capture.py --attach

# Detach webcam (give back to Windows)
python3 webcam_capture.py --detach
```

## Architecture

```
Windows (USB webcam) --USBIP--> WSL2 (vhci_hcd) --V4L2--> ustreamer --> HTTP MJPEG stream --> curl/Python/OpenCV
```

## Notes

- 640x480 is the stable resolution over USBIP (1080p tends to drop frames)
- The stream runs at `http://127.0.0.1:8080`
- Snapshot endpoint: `http://127.0.0.1:8080/snapshot`
- For video recording, pipe the MJPEG stream to ffmpeg
- Audio: the Realtek USB audio device can also be passed through on busid 4-5
