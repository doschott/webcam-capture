import subprocess, os, sys

# Find ffmpeg
ffmpeg_paths = [
    r"C:\Users\doschott\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    r"C:\ffmpeg\bin\ffmpeg.exe",
]
FFMPEG = None
for p in ffmpeg_paths:
    if os.path.exists(p):
        FFMPEG = p
        break

if FFMPEG is None:
    r = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        FFMPEG = r.stdout.strip().split()[0]

if FFMPEG is None:
    print("ERROR: ffmpeg not found. Install: winget install Gyan.FFmpeg")
    sys.exit(1)

OUTPUT = r"C:\Users\Public\video.mp4"
DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 5

cmd = [
    FFMPEG,
    "-f", "dshow",
    "-rtbufsize", "100M",
    "-i", "video=Brio 100:audio=Microphone (Brio 100)",
    "-t", str(DURATION),
    "-c:v", "libx264", "-preset", "ultrafast",
    "-c:a", "aac",
    "-y", OUTPUT
]

print(f"Recording {DURATION}s...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("ERROR:", r.stderr[-500:] if r.stderr else "Unknown")
    sys.exit(1)

size = os.path.getsize(OUTPUT)
print(f"OK: {size} bytes, {DURATION}s")
