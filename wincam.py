import cv2, os, sys
O = r"C:\Users\Public\webcam_capture.jpg"
c = cv2.VideoCapture(0, cv2.CAP_ANY)
c.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
c.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
c.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
if not c.isOpened():
    print("ERROR: Cannot open camera")
    sys.exit(1)
r, f = c.read()
c.release()
if not r:
    print("ERROR: Failed to capture frame")
    sys.exit(1)
cv2.imwrite(O, f)
print("OK: %dx%d, %d bytes" % (f.shape[1], f.shape[0], os.path.getsize(O)))
