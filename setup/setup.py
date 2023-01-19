import cv2

cap = cv2.VideoCapture(1)
w, h = int(cap.get(3)), int(cap.get(4))

framespersecond = int(cap.get(cv2.CAP_PROP_FPS))
print("FPS: ", framespersecond)

line_thicknes = 1

while True:
    ret, frame = cap.read()
    frame = cv2.resize(frame, (w, h))
    cv2.line(frame, (w // 2, 0), (w // 2, h), (0, 0, 255), line_thicknes)
    cv2.imshow('Setup', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
