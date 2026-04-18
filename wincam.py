import cv2, os, sys
O = r"C:\Users\Public\webcam_capture.jpg"
c = cv2.VideoCapture(0)
c.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# Warm up - let auto-exposure settle
for _ in range(5):
    c.read()
r, f = c.read()
c.release()
if not r:
    print("ERROR")
    sys.exit(1)
cv2.imwrite(O, f)
print("OK: %dx%d" % (f.shape[1], f.shape[0]))
