import cv2, os, sys

OUTPUT = r"C:\Users\Public\claw-webcam-capture\image\webcam_capture.jpg"
c = cv2.VideoCapture(0)
c.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
for _ in range(5):
    c.read()
r, f = c.read()
c.release()
if not r:
    print("ERROR")
    sys.exit(1)
cv2.imwrite(OUTPUT, f)
print("OK: %s (%dx%d)" % (OUTPUT, f.shape[1], f.shape[0]))
