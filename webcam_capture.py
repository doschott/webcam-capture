#!/usr/bin/env python3
"""
Webcam Capture Tool for WSL2 + USBIP
Captures images, video frames from a webcam attached to Windows,
accessed from WSL2 via USBIP using ustreamer as the streaming engine.

Usage:
    python3 webcam_capture.py --status
    python3 webcam_capture.py --attach
    python3 webcam_capture.py --start
    python3 webcam_capture.py --capture output.jpg
    python3 webcam_capture.py --watch --fps 5
"""
import subprocess
import time
import os
import argparse

DEVICE = "/dev/video0"
DEFAULT_PORT = 8080

_WSL = "/mnt/c/Windows/System32/wsl.exe"
_PS = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


def _wsl(cmd: str) -> str:
    r = subprocess.run([_WSL, "--user", "root", "-e", "sh", "-c", cmd],
        capture_output=True, text=True, timeout=15)
    return r.stdout + r.stderr


def _ps(cmd: str) -> str:
    r = subprocess.run([_PS, "-Command", cmd], capture_output=True, text=True, timeout=15)
    return r.stdout + r.stderr


def _wsl_bg(cmd: str) -> None:
    subprocess.Popen([_WSL, "--user", "root", "-e", "sh", "-c", cmd],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _ps_bg(cmd: str) -> None:
    subprocess.Popen([_PS, "-Command", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_device_present() -> bool:
    return os.path.exists(DEVICE) or "OK" in _wsl(f"ls {DEVICE} 2>/dev/null && echo OK")


def is_streaming(port: int) -> bool:
    url = f"http://127.0.0.1:{port}/snapshot"
    try:
        r = subprocess.run(["curl", "-s", "--connect-timeout", "2", url, "-o", "/dev/null"],
                            capture_output=True, timeout=5)
        return r.returncode == 0
    except:
        return False


def attach(busid: str = "4-1") -> bool:
    if is_device_present():
        print("Device already present")
        return True
    print(f"Attaching {busid}...")
    _ps_bg(f"usbipd attach --wsl --busid {busid}")
    time.sleep(3)
    if is_device_present():
        print("Attached!")
        return True
    print("Attach may have failed")
    return False


def detach(busid: str = "4-1") -> None:
    _ps_bg(f"usbipd detach --busid {busid}")
    print(f"Detached {busid}")


def stop_stream(port: int) -> None:
    _wsl("killall ustreamer 2>/dev/null; echo done")
    time.sleep(1)


def start_stream(port: int, resolution: str = "640x480") -> bool:
    if is_streaming(port):
        print(f"Stream already running on port {port}")
        return True
    
    _wsl(f"chmod 666 {DEVICE}")
    stop_stream(port)
    time.sleep(1)
    
    cmd = (f"nohup ustreamer --device {DEVICE} "
           f"--resolution {resolution} --format MJPEG "
           f"--host 0.0.0.0 --port {port} "
           f"> /tmp/ustreamer.log 2>&1 &")
    _wsl_bg(cmd)
    
    # Wait for "Capturing started" (up to 30s)
    for i in range(30):
        time.sleep(1)
        log = _wsl("tail -5 /tmp/ustreamer.log 2>/dev/null")
        if "Capturing started" in log:
            print(f"Streaming on port {port} at {resolution}")
            return True
        if "Can't open device" in log:
            print("Device not available")
            return False
    
    # Still try - it might be retrying
    if is_streaming(port):
        print(f"Stream running on port {port}")
        return True
    print("Warning: capturing may not have started yet")
    return True


def capture(output: str, port: int, timeout: int = 8) -> bool:
    if not is_streaming(port):
        print("Stream not running. Run --start first.")
        return False
    url = f"http://127.0.0.1:{port}/snapshot"
    try:
        r = subprocess.run(["curl", "-s", "--connect-timeout", str(timeout), url, "-o", output],
                           capture_output=True, timeout=timeout + 2)
        if not os.path.exists(output):
            return False
        sz = os.path.getsize(output)
        if sz < 1000:
            os.remove(output)
            return False
        print(f"Captured: {output} ({sz} bytes)")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def status(port: int) -> None:
    dev = is_device_present()
    strm = is_streaming(port)
    print(f"Device: {'OK' if dev else 'MISSING'}")
    print(f"Stream (port {port}): {'RUNNING' if strm else 'STOPPED'}")
    if strm:
        log = _wsl("tail -3 /tmp/ustreamer.log 2>/dev/null")
        if "Capturing started" in log:
            print("Capture: ACTIVE")


def main() -> None:
    p = argparse.ArgumentParser(description="Webcam Capture for WSL2 + USBIP")
    p.add_argument("--status", action="store_true", help="Check status")
    p.add_argument("--start", action="store_true", help="Start stream")
    p.add_argument("--stop", action="store_true", help="Stop stream")
    p.add_argument("--capture", metavar="FILE", help="Capture snapshot")
    p.add_argument("--attach", action="store_true", help="Attach webcam")
    p.add_argument("--detach", action="store_true", help="Detach webcam")
    p.add_argument("--busid", default="4-1", help="USB busid (default: 4-1)")
    p.add_argument("--resolution", default="640x480", help="Resolution (default: 640x480)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    p.add_argument("--watch", action="store_true", help="Watch mode")
    p.add_argument("--fps", type=int, default=5, help="Watch FPS (default: 5)")
    p.add_argument("--install", action="store_true", help="Install packages")
    
    args = p.parse_args()
    port = args.port
    
    if args.install:
        print("Installing packages...")
        _wsl("apt-get update -qq && apt-get install -y --no-install-recommends "
             "ustreamer ffmpeg v4l-utils gstreamer1.0-tools gstreamer1.0-plugins-good")
        print("Done")
        return
    
    if args.status:
        status(port)
    
    if args.attach:
        attach(args.busid)
    
    if args.detach:
        stop_stream(port)
        detach(args.busid)
    
    if args.start:
        if not is_device_present():
            print("Device missing. Run --attach first.")
            return
        start_stream(port, args.resolution)
    
    if args.stop:
        stop_stream(port)
        print("Stopped")
    
    if args.capture:
        capture(args.capture, port)
    
    if args.watch:
        if not is_streaming(port):
            print("Stream not running. Run --start first.")
            return
        print(f"Watching at {args.fps} fps...")
        i = 0
        try:
            while True:
                path = f"/tmp/w{i:04d}.jpg"
                if capture(path, port):
                    print(f"  {i}: {os.path.getsize(path)}b")
                i += 1
                time.sleep(1.0 / args.fps)
        except KeyboardInterrupt:
            print(f"\n{i} frames")
    
    if not any([args.status, args.start, args.stop, args.capture, args.attach,
                 args.detach, args.watch, args.install]):
        p.print_help()


if __name__ == "__main__":
    main()
