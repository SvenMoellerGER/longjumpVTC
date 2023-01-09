import datetime
import os
import sys
import time
import multitimer
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


##### Aufgabe 1: Videoaufnahme
# TODO: Video
#  Aufnahme durch Klick des Users starten (Anlage freigegeben oder Athlet beginnt Versuch)
def capture_video():
    global w, h, cap
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera kann nicht geöffnet werden!")
        exit()
    w, h = int(cap.get(3)), int(cap.get(4))
    new_vid_file()
    capture = True
    timer.start()
    while capture:
        if len(vidList) > 3:
            vidList.pop(0)
        ret, frame = cap.read()
        if not ret:
            print("Frame kann nicht empfangen werden (Stream beendet?)")
            break
        # Frame bearbeiten
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        out.write(frame)
    cap.release()
    cv2.destroyAllWindows()


def new_interval_video():
    out.release()
    new_vid_file()


secs = 2
timer = multitimer.MultiTimer(interval=secs, function=new_interval_video)


##### Aufgabe 2: Serielle Schnittstelle überwachen, Messung überprüfen // Schwellwert, Trigger
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
                    print('getSecondCam ausgeführt')
                    getSecondCam()
                else:
                    trigger = False
                if trigger:
                    print('Trigger successful')
                    time.sleep(secs + 0.3)
                    # out.release()
                    # cap.release()
                    cv2.destroyAllWindows()
                    extract_frames()
                    break
            if isinstance(decoded_bytes, str):
                print(decoded_bytes)
        except serial.SerialException:
            ex = sys.exc_info()
            print(ex)
            break


def extract_frames():
    fileDir = os.getcwd()
    path = os.path.join(fileDir, 'processing', 'triggered', triggeredTime)
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    count = 1
    for i in range(len(vidList)):
        vid = cv2.VideoCapture('processing/videos/'+vidList[i])
        success, image = vid.read()
        print(vidList[i])
        while success:
            line_thicknes = 1
            cv2.line(image, (w//2, 0), (w//2, h), (0, 0, 255), line_thicknes)
            cv2.imwrite(os.path.join(path, triggeredTime + '_frame%04d.jpg' % count), image)
            success, image = vid.read()
            count += 1
        i += 1
    print('\nALLES ERLEDIGT')


def setupSecondCam():
    try:
        global frame_ipcam

        user = 'tapoc100'
        password = user
        ipaddress = '192.168.178.37'
        rtspPort = '554'
        resolution = '/stream1'

        cap_ipcam = cv2.VideoCapture('rtsp://' + user + ':' + password + '@' + ipaddress + ':' + rtspPort + resolution)
        breite, hoehe = int(cap_ipcam.get(3)), int(cap_ipcam.get(4))
        print('cap_ipcam gestartet')

        while True:
            funzt, frame_ipcam = cap_ipcam.read()
            frame_ipcam = cv2.resize(frame_ipcam, (breite, hoehe))

    except:
        print('Bilder der zweiten Kamera konnte nicht empfangen werden!')
        print(sys.exc_info())


def getSecondCam():
    fileDir = os.getcwd()
    path = os.path.join(fileDir, 'processing', 'triggered', triggeredTime)
    os.mkdir(path)
    path_secondCam = os.path.join(path, triggeredTime + '_secondCamTriggered.jpg')
    cv2.imwrite(path_secondCam, frame_ipcam)


thread_captureVid = threading.Thread(target=capture_video, args=())
thread_captureVid.start()

thread_listenSerial = threading.Thread(target=trigger_serial, args=())
thread_listenSerial.start()

thread_setupSecondCam = threading.Thread(target=setupSecondCam, args=())
thread_setupSecondCam.start()
