# Webcam Capture for WSL2

Capture images from a Logitech Brio 100 webcam using WSL2.

## ⚠️ Important: USBIP Does NOT Work for Video

WSL2's USBIP driver (`vhci_hcd`) cannot handle **isochronous USB transfers** — the high-bandwidth, low-latency transfers webcams use for video. You'll get placeholder images (~13KB with EXIF metadata, no real pixels) and `urb->status -104` errors in dmesg.

## Working Method: Windows DirectShow

Capture via Windows OpenCV, save to `C:\Users\Public\` (accessible from WSL).

### Setup

**Windows:**
```powershell
winget install Python.Python.3.12
python -m pip install opencv-python-headless
```

**Copy the capture script:**
```bash
# The script is at /tmp/wincam.py
cp /tmp/wincam.py /mnt/c/Users/Public/wincam.py
```

### Capture

```powershell
# From PowerShell:
& 'C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\Public\wincam.py'

# From WSL, copy the result:
cp /mnt/c/Users/Public/webcam_capture.jpg output.jpg
```

### Windows Script (`wincam.py`)
```python
import cv2, os, sys
O = r"C:\Users\Public\webcam_capture.jpg"
c = cv2.VideoCapture(0, cv2.CAP_ANY)
c.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
c.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
c.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
if not c.isOpened(): print("ERROR"); sys.exit(1)
r, f = c.read()
c.release()
if not r: print("ERROR"); sys.exit(1)
cv2.imwrite(O, f)
print("OK: %dx%d" % (f.shape[1], f.shape[0]))
```

## USBIP for Future Reference

USBIP shows the device as "Shared" (not "Attached") while Windows uses it. To share with WSL:

```powershell
# In PowerShell as Admin:
usbipd list  # Find the Brio 100 busid (4-1)
usbipd bind --busid 4-1
usbipd attach --wsl --busid 4-1   # Attaches to WSL (video won't work)
usbipd detach --busid 4-1         # Returns to Windows
```

**Busids:**
- Brio 100: 4-1 (046d:094c)
- Realtek USB Audio: 4-5 (0db0:543d)

## Architecture

```
Working: Windows DirectShow -> OpenCV -> C:\Users\Public\ -> /mnt/c/ -> WSL
Broken:  Windows USB -> USBIP -> WSL vhci_hcd -> V4L2 -> ustreamer (isochronous fails)
```

## Key Finding

The webcam light being "on" means the USB connection works (device enumeration, descriptors, control transfers all fine). But actual video data requires isochronous transfers, which WSL2's USBIP implementation cannot deliver reliably.
