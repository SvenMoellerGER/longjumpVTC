import datetime
import os
import sys
import serial
import cv2
import threading

global vidList
vidList = []


class CustomError(Exception):
    pass


def new_vid_file():
    global out
    fileName = get_time(0)
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    out = cv2.VideoWriter('processing/videos/'+fileName+'.mp4', fourcc, 60.0, (w, h))
    vidList.append(fileName+'.mp4')


def get_time(style):
    t = datetime.datetime.now()
    if style == 0:  # Tag mit Zeit
        t = t.strftime('%Y%m%d-%H%M%S_%f')[:-3]
    elif style == 1:    # Zeit
        t = t.strftime('%S.%f')[:-3]
    else:
        raise ValueError('0 oder 1 erforderlich!')
    return t


##### task 1: Video capture
# TODO: Video
#  start saving on click (attempt started)
def capture_video():
    global w, h
    cap = cv2.VideoCapture(0)
    w, h = int(cap.get(3)), int(cap.get(4))
    startTime = get_time(1)
    new_vid_file()
    capture = True
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    while capture:
        if len(vidList) > 3:
            vidList.pop(0)
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?)")
            break
        # operations on frame
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # display the frame
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(1) == ord('q'):
        #     break
        out.write(frame)
        currentTime = get_time(1)
        breakDecision = float(currentTime) - float(startTime)
        print('currentTime: ' + str(currentTime))       # for debugging
        print('startTime: ' + str(startTime))       # for debugging
        print('breakDecision: ' + str(breakDecision))       # for debugging
        if breakDecision > 5.0:
            out.release()
            new_vid_file()
            startTime = currentTime
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()


##### task 2: listen to serial, check measurement // threshold, set trigger
def trigger_serial():
    global triggeredTime

    ser = serial.Serial(port='COM4',
                        baudrate=115200,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        bytesize=serial.EIGHTBITS
                        )
    ser.flushInput()

    while True:
        try:
            ser_bytes = ser.readline()
            decoded_bytes = ser_bytes.decode("utf-8")
            try:
                decoded_bytes = int(decoded_bytes)
            except:
                pass
            if isinstance(decoded_bytes, int):
                if decoded_bytes < 1300:  # 1.30 Meter (ungefähr Breite des Absprungbrettes)
                    trigger = True
                    triggeredTime = get_time(0)
                else:
                    trigger = False
                decoded_bytes = str(decoded_bytes)
                print(decoded_bytes)
                if trigger:
                    print('Trigger successful')
                    extract_frames()
                    break
            print(decoded_bytes)
        except serial.SerialException:
            ex = sys.exc_info()
            print(ex)
            break


# TODO: processing
#  trigger frame == number 1000

def extract_frames():
    fileDir = os.getcwd()
    path = os.path.join(fileDir, 'processing', 'triggered', triggeredTime)
    os.mkdir(path)
    count = 1000
    for i in range(len(vidList)):
        vid = cv2.VideoCapture('processing/videos/'+vidList[i])
        success, image = vid.read()
        while success:
            line_thicknes = 1
            cv2.line(image, (w//2, 0), (w//2, h), (0, 0, 255), line_thicknes)
            cv2.imwrite(os.path.join(path, triggeredTime + '_frame%d.jpg' % count), image)
            success, image = vid.read()
            count += 1
        i += 1


thread_captureVid = threading.Thread(target=capture_video, args=())
thread_captureVid.start()

thread_listenSerial = threading.Thread(target=trigger_serial, args=())
thread_listenSerial.start()
