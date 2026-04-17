# Webcam Capture for WSL2 + USBIP

Capture images, video, and audio from a webcam attached to Windows, accessed from WSL2 via USBIP.

## Quick Start

```bash
cd /home/dosubuntu/clawd/projects/webcam-capture

# Check what's connected
python3 webcam_capture.py --status

# Attach webcam (if not already attached via Windows USBIP)
python3 webcam_capture.py --attach

# Start the MJPEG stream server
python3 webcam_capture.py --start

# Capture a photo
python3 webcam_capture.py --capture photo.jpg

# Watch mode (5 fps continuous)
python3 webcam_capture.py --watch --fps 5

# Stop stream
python3 webcam_capture.py --stop

# Detach webcam (give back to Windows)
python3 webcam_capture.py --detach
```

## Workflow

```
Windows (USB webcam) --USBIP--> WSL2 (vhci_hcd) --V4L2--> ustreamer --> HTTP MJPEG --> curl --> image file
```

## Architecture

- **ustreamer**: Lightweight MJPEG-HTTP streamer running in WSL2
- **USBIP**: Shares USB device from Windows to WSL2
- **Snapshot**: `curl http://127.0.0.1:8080/snapshot` grabs one frame
- **Video**: Pipe MJPEG stream to ffmpeg to record `.mp4`

## Windows Setup (one-time)

```powershell
winget install usbipd
# Reboot Windows
# In PowerShell (Admin):
usbipd list
# Find your webcam (e.g. Brio 100 on busid 4-1)
usbipd bind --busid 4-1
usbipd attach --wsl --busid 4-1
```

## WSL Setup (one-time)

```bash
python3 webcam_capture.py --install
```

Or manually:
```bash
sudo apt update && sudo apt install ustreamer ffmpeg v4l-utils
```

## Notes

- **Resolution**: 640x480 is the stable default. The Logitech Brio 100 supports up to 1080p but high-res can drop frames over USBIP.
- **Busids**: Logitech Brio 100 is `4-1`, Realtek Audio is `4-5`
- **Port**: Default is 8080. Use `--port N` to change.
- **Warning**: The "Can't set input channel" log message is normal — ustreamer retries and capturing starts within a few seconds.
- **Stopping**: `killall ustreamer` stops the stream but keeps the USBIP device attached.
- **Audio**: The Realtek USB audio device on busid `4-5` can also be passed through for audio capture.

## Tool Reference

| Flag | Description |
|------|-------------|
| `--status` | Show device and stream status |
| `--attach` | Attach webcam via USBIP |
| `--detach` | Detach webcam (return to Windows) |
| `--start` | Start ustreamer stream |
| `--stop` | Stop ustreamer stream |
| `--capture FILE` | Save snapshot to FILE |
| `--watch` | Continuous capture mode |
| `--fps N` | Frames per second for watch mode |
| `--resolution WxH` | Stream resolution |
| `--port N` | HTTP server port |
| `--busid ID` | USB busid of device |
| `--install` | Install required packages |
