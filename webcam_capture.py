#!/usr/bin/env python3
"""
Webcam Capture Tool for WSL2 + USBIP
Uses ustreamer to stream/capture from USB webcam over USBIP.

Setup:
1. Windows side: winget install usbipd
2. WSL side: apt install ustreamer (already done)
3. Attach: python webcam_capture.py --attach
4. Start stream: python webcam_capture.py --start
5. Capture: python webcam_capture.py --capture /path/to/output.jpg
"""
import subprocess
import time
import os
import argparse

USTREAMER_PORT = 8080
SNAPSHOT_URL = f"http://127.0.0.1:{USTREAMER_PORT}/snapshot"
STREAM_URL = f"http://127.0.0.1:{USTREAMER_PORT}/stream"
DEVICE = "/dev/video0"
LOG_FILE = "/tmp/webcam_capture.log"

_wsl = "/mnt/c/Windows/System32/wsl.exe"
_ps = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"


def _run_wsl(cmd: str, shell: bool = False) -> str:
    if shell:
        result = subprocess.run(f"{_wsl} --user root -e {cmd}",
            capture_output=True, text=True, timeout=15, shell=True)
    else:
        result = subprocess.run([_wsl, "--user", "root", "-e"] + cmd.split(),
            capture_output=True, text=True, timeout=15)
    return result.stdout + result.stderr


def _run_ps(args: str) -> str:
    result = subprocess.run([_ps, "-Command", args],
        capture_output=True, text=True, timeout=15)
    return result.stdout + result.stderr


def is_stream_running() -> bool:
    try:
        r = subprocess.run(["curl", "-s", "--connect-timeout", "2",
                           SNAPSHOT_URL, "-o", "/dev/null"],
                          capture_output=True, timeout=5)
        return r.returncode == 0 and len(r.stdout) > 0
    except:
        return False


def start_streamer(resolution="640x480", port=USTREAMER_PORT):
    if is_stream_running():
        print(f"Stream already running on port {port}")
        return True
    
    _run_wsl(f"chmod 666 {DEVICE}")
    _run_wsl("pkill ustreamer 2>/dev/null || true")
    time.sleep(1)
    
    # Kill process on the port first
    _run_wsl(f"fuser -k {port}/tcp 2>/dev/null || true")
    time.sleep(1)
    
    # Start ustreamer
    cmd = (f"cd /tmp && nohup ustreamer --device {DEVICE} "
           f"--resolution {resolution} --format MJPEG "
           f"--host 0.0.0.0 --port {port} > /tmp/ustreamer.log 2>&1 &")
    _run_wsl(cmd)
    
    for i in range(10):
        time.sleep(1)
        if is_stream_running():
            print(f"ustreamer streaming on port {port}")
            return True
    
    log = _run_wsl("cat /tmp/ustreamer.log", shell=True)
    print(f"Failed to start. Log:\n{log[-500:]}")
    return False


def stop_streamer():
    _run_wsl("pkill -f ustreamer || true")
    print("Stream stopped")


def attach(busid="4-1"):
    if _run_wsl(f"ls {DEVICE}", shell=True) != "":
        print("Device already attached")
        return True
    print(f"Attaching {busid}...")
    _run_ps(f"usbipd attach --wsl --busid {busid}")
    time.sleep(3)
    if _run_wsl(f"ls {DEVICE}", shell=True) != "":
        print("Attached!")
        return True
    print("Attach may have failed - check status")
    return False


def detach(busid="4-1"):
    _run_ps(f"usbipd detach --busid {busid}")
    print("Detached")


def status():
    dev = "/dev/video0" in _run_wsl("ls /dev/video*", shell=True)
    strm = is_stream_running()
    print(f"Device: {'OK' if dev else 'MISSING'}")
    print(f"Stream: {'RUNNING' if strm else 'STOPPED'}")
    if dev:
        info = _run_wsl(f"v4l2-ctl --device={DEVICE} --info 2>/dev/null", shell=True)
        if info:
            print(info[:400])


def capture(output="/tmp/webcam_shot.jpg", timeout=5):
    if not is_stream_running():
        print("Stream not running. Run --start first.")
        return False
    try:
        r = subprocess.run(["curl", "-s", "--connect-timeout", str(timeout),
                           SNAPSHOT_URL, "-o", output],
                          capture_output=True, timeout=timeout+2)
        sz = os.path.getsize(output) if os.path.exists(output) else 0
        if sz > 1000:
            print(f"Captured: {output} ({sz} bytes)")
            return True
        print("Frame too small or missing")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    p = argparse.ArgumentParser(description="Webcam Capture Tool")
    p.add_argument("--start", action="store_true", help="Start streaming server")
    p.add_argument("--stop", action="store_true", help="Stop streaming server")
    p.add_argument("--capture", metavar="FILE", help="Capture snapshot to FILE")
    p.add_argument("--attach", action="store_true", help="Attach webcam via USBIP")
    p.add_argument("--detach", action="store_true", help="Detach webcam via USBIP")
    p.add_argument("--status", action="store_true", help="Check device and stream status")
    p.add_argument("--resolution", default="640x480", help="Stream resolution (default: 640x480)")
    p.add_argument("--busid", default="4-1", help="USB busid (default: 4-1)")
    p.add_argument("--watch", action="store_true", help="Watch mode: capture frames continuously")
    p.add_argument("--fps", type=int, default=5, help="FPS for watch mode (default: 5)")
    p.add_argument("--install", action="store_true", help="Install ustreamer in WSL")
    args = p.parse_args()

    if args.install:
        print("Installing ustreamer...")
        _run_wsl("apt-get update -qq && apt-get install -y --no-install-recommends ustreamer gstreamer1.0-plugins-good")
        print("Done")
        return

    if args.status:
        status()

    if args.attach:
        attach(args.busid)

    if args.detach:
        detach(args.busid)

    if args.start:
        dev_result = _run_wsl("ls /dev/video*", shell=True)
        if "/dev/video0" not in dev_result:
            print("Device missing. Run --attach first.")
            return
        start_streamer(resolution=args.resolution)

    if args.stop:
        stop_streamer()

    if args.capture:
        capture(args.capture)

    if args.watch:
        if not is_stream_running():
            print("Stream not running. Run --start first.")
            return
        i = 0
        print(f"Watching at {args.fps} fps...")
        while True:
            path = f"/tmp/webcam_{i:04d}.jpg"
            if capture(path):
                print(f"  Frame {i}: {os.path.getsize(path)} bytes")
            i += 1
            time.sleep(1.0 / args.fps)

    if not any([args.start, args.stop, args.capture, args.attach,
                 args.detach, args.status, args.watch, args.install]):
        p.print_help()


if __name__ == "__main__":
    main()
