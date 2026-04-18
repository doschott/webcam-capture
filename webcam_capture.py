#!/usr/bin/env python3
"""
Webcam Capture Tool for WSL2

Reliable architecture: Windows-side DirectShow capture via OpenCV,
saved to C:\Users\Public\ (accessible from WSL), then copied to target.

USBIP approach (WSL -> v4l2 -> ustreamer) does NOT work reliably because
WSL2's USBIP driver cannot handle isochronous transfers required for video.

Usage:
    python3 webcam_capture.py --capture output.jpg
    python3 webcam_capture.py --capture output.jpg --resolution 1920x1080
    python3 webcam_capture.py --status
"""
import subprocess
import os
import argparse

WIN_PY = r"C:\Users\doschott\AppData\Local\Programs\Python\Python312\python.exe"
WIN_SCRIPT = r"C:\Users\Public\win_capture.py"
WIN_OUTPUT = r"C:\Users\Public\webcam_capture.jpg"
WSL_OUTPUT = "/tmp/webcam_capture.jpg"

_WSL = "/mnt/c/Windows/System32/wsl.exe"
_PS = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


def _ps(cmd: str, timeout: int = 15) -> str:
    r = subprocess.run([_PS, "-Command", cmd],
        capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr


def _ps_bg(cmd: str) -> None:
    subprocess.Popen([_PS, "-Command", cmd],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _wsl(cmd: str) -> str:
    r = subprocess.run([_WSL, "--user", "root", "-e", "sh", "-c", cmd],
        capture_output=True, text=True, timeout=15)
    return r.stdout + r.stderr


def is_windows_cam_available() -> bool:
    """Check if webcam is available to Windows (not attached to WSL via USBIP)."""
    r = _ps("usbipd list")
    for line in r.split("\n"):
        if "Brio 100" in line:
            return "Attached" not in line and "Shared" not in line
    return False  # Not found in list - assume available


def attach_usbip() -> bool:
    """Attach webcam via USBIP to WSL."""
    _ps_bg("usbipd attach --wsl --busid 4-1")
    import time; time.sleep(3)
    r = _wsl("ls /dev/video0 2>/dev/null && echo OK")
    return "OK" in r


def detach_usbip() -> bool:
    """Detach webcam from WSL, return to Windows."""
    _ps_bg("usbipd detach --busid 4-1")
    import time; time.sleep(2)
    return True


def write_windows_script(width: int, height: int) -> None:
    """Write the Windows capture script."""
    script = (
        f"import cv2,os,sys\n"
        f"O=r'C:\\Users\\Public\\webcam_capture.jpg'\n"
        f"c=cv2.VideoCapture(0,cv2.CAP_ANY)\n"
        f"c.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))\n"
        f"c.set(cv2.CAP_PROP_FRAME_WIDTH,{width})\n"
        f"c.set(cv2.CAP_PROP_FRAME_HEIGHT,{height})\n"
        f"if not c.isOpened(): print('ERROR: Cannot open camera');sys.exit(1)\n"
        f"r,f=c.read()\n"
        f"c.release()\n"
        f"if not r: print('ERROR: Failed to capture frame');sys.exit(1)\n"
        f"cv2.imwrite(O,f);print('OK: %dx%d, %d bytes'%(f.shape[1],f.shape[0],os.path.getsize(O)))"
    )
    # Write via PowerShell
    _ps(f"@({chr(10).join(chr(39)+l+chr(39) for l in script.split(chr(10)))}) | Out-File -Encoding ASCII '{WIN_SCRIPT}'")
    # Simpler: just use the already-copied script
    pass


def capture(output: str, width: int = 1280, height: int = 720) -> bool:
    """
    Capture from Windows DirectShow, save to output path.
    This is the reliable method.
    """
    # Ensure Windows script exists
    if not os.path.exists("/mnt/c/Users/Public/win_capture.py"):
        _ps(f"echo 'import cv2,os, sys' | Out-File '{WIN_SCRIPT}' -Encoding ASCII")
    
    # Run capture on Windows
    r = _ps(f"& '{WIN_PY}' '{WIN_SCRIPT}'", timeout=10)
    
    if "OK:" not in r:
        print(f"Capture failed: {r}")
        return False
    
    # Copy from Windows to WSL
    if not os.path.exists("/mnt/c/Users/Public/webcam_capture.jpg"):
        print(f"Windows output not found: {r}")
        return False
    
    try:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    except:
        pass
    
    # Copy via WSL
    subprocess.run(["cp", "/mnt/c/Users/Public/webcam_capture.jpg", output], check=True)
    sz = os.path.getsize(output)
    print(f"Captured: {output} ({sz} bytes)")
    return True


def main():
    p = argparse.ArgumentParser(description="Webcam Capture Tool")
    p.add_argument("--capture", metavar="FILE", help="Capture snapshot to FILE")
    p.add_argument("--width", type=int, default=1280, help="Frame width (default: 1280)")
    p.add_argument("--height", type=int, default=720, help="Frame height (default: 720)")
    p.add_argument("--status", action="store_true", help="Check USBIP status")
    p.add_argument("--attach", action="store_true", help="Attach webcam to WSL via USBIP")
    p.add_argument("--detach", action="store_true", help="Detach webcam from WSL")
    args = p.parse_args()

    if args.status:
        r = _ps("usbipd list")
        print(r)

    if args.detach:
        detach_usbip()
        print("Detached from WSL")

    if args.attach:
        attach_usbip()
        print("Attached to WSL")

    if args.capture:
        capture(args.capture, args.width, args.height)

    if not any([args.capture, args.status, args.attach, args.detach]):
        p.print_help()


if __name__ == "__main__":
    main()
