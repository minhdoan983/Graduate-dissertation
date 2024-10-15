import sys
sys.path.append('/usr/lib/python3/dist-packages')  # Them thu muc vao sys.path de tim kiem cac goi thu vien
from picamera2 import Picamera2 as PiCamera, Preview  # Import thu vien de su dung camera
import time  # Thu vien de su dung cac ham lien quan den thoi gian
import cv2  # Thu vien OpenCV cho xu ly anh
from ultralytics import YOLO  # Thu vien YOLO cho nhan dang doi tuong
import RPi.GPIO as GPIO  # Thu vien RPi.GPIO de dieu khien cac chan GPIO tren Raspberry Pi
import serial  # Thu vien de giao tiep voi cac thiet bi qua cong serial
import requests  # Thu vien de gui cac yeu cau HTTP
from requests.exceptions import RequestException, Timeout  # Thu vien de xu ly cac ngoai le cua requests
from pyzbar import pyzbar  # Thu vien de doc ma vach
import numpy as np  # Thu vien numpy cho xu ly so hoc

# Khoi tao model YOLO
model = YOLO("/home/pi/Downloads/yolo_8/runs/detect/train/weights/best.pt")

# Dat che do chan GPIO
GPIO.setmode(GPIO.BCM)

# Dinh nghia cac chan GPIO
button_capture_pin = 17  
button_barcode_pin = 22
button_send_pin = 27  
switch_pin = 22
led1_pin = 12  # GPIO 18
led2_pin = 16  # GPIO 23
led3_pin = 26  # GPIO 23
buzzer_pin = 5

# Dat chan GPIO va keo len
GPIO.setup(button_capture_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_send_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_barcode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led1_pin, GPIO.OUT)
GPIO.setup(led2_pin, GPIO.OUT)
GPIO.setup(led3_pin, GPIO.OUT)
GPIO.setup(buzzer_pin, GPIO.OUT)

# Khoi tao camera
camera = PiCamera()

# Cai dat do phan giai camera
camera_config = camera.create_still_configuration(
    main={"size": (2592, 1944)},  # Kich thuoc anh chinh
    lores={"size": (640, 480)}  # Kich thuoc anh thap hon
)

camera.configure(camera_config)  # Cau hinh camera
camera.start_preview(Preview.DRM)  # Bat dau xem truoc camera
camera.start()  # Bat dau camera

# Khoi tao video capture
cap = cv2.VideoCapture(0)
last_result = None
button_pressed = False
product_id = None
loadcell_value = None
COLOR = False

while True:
    # Kiem tra trang thai nut bam chup anh
    if GPIO.input(button_capture_pin) == GPIO.LOW:
        print("Button 1 on.")
        GPIO.output(led1_pin, GPIO.HIGH)  # Bat den LED 1
        # Chup anh va luu lai
        camera.capture_file("capture.jpg")
        # Doc anh tu file
        image = cv2.imread("capture.jpg")
        # Nhan dang doi tuong tu yolov8
        results = model.predict(source=image, save=True)
        # Xu ly ket qua va doc gia tri loadcell
        if results:
            highest_confidence = -1  # Bien luu do chinh xac cao nhat
            loadcell_value = None  # Bien luu gia tri loadcell

            for result in results:
                boxes = result.boxes
                if boxes:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0]  # Toa do hop bao
                        conf = box.conf[0]  # Do chinh xac
                        cls = int(box.cls[0])  # Lop doi tuong
                        if cls >= 0 and conf > highest_confidence:  # Kiem tra neu lop duoc gan co do chinh xac cao hon
                            highest_confidence = conf
                            product_id = int(box.cls)

            if product_id is not None:
                print(f"Label: {product_id}, Confidence: {highest_confidence:.2f}")

                # Ket noi den serial port va doc gia tri loadcell
                ser = serial.Serial('/dev/ttyUSB0', 9600)
                loadcell_value = ser.readline().decode('utf-8').strip()
                print(f"Loadcell value: {loadcell_value}")
        
        GPIO.output(led1_pin, GPIO.LOW)  # Tat den LED 1
        GPIO.output(led2_pin, GPIO.LOW)  # Tat den LED 2
                        
    time.sleep(0.5)
    button_state = GPIO.input(button_barcode_pin)

    # Kiem tra trang thai nut bam doc barcode
    if button_state == GPIO.LOW:
        if not button_pressed:
            print("Button 2 on.")
            GPIO.output(led3_pin, GPIO.HIGH)  # Bat den LED 3
            print("LED 2 ON")
            button_pressed = True
    else:
        if button_pressed:
            print("Button 2 released.")
            GPIO.output(led3_pin, GPIO.LOW)  # Tat den LED 3
            GPIO.output(led1_pin, GPIO.LOW)  # Tat den LED 1
            button_pressed = False
            cv2.destroyAllWindows()  # Tat tat ca cac cua so hien thi

    if button_pressed:
        ret, frame = cap.read()  # Doc khung hinh tu camera
        frame = camera.capture_array()  # Chup anh tu camera
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Chuyen anh sang gray
        # cv2.imshow("Gray Image", gray_frame)
        barcodes = pyzbar.decode(gray_frame)  # Doc ma vach tu anh gray

        for barcode in barcodes:
            loadcell_value = 1 
            barcodeData = barcode.data.decode("utf-8")  # Lay du lieu ma vach
            barcodeType = barcode.type  # Lay loai ma vach
            (x, y, w, h) = barcode.rect  # Toa do hop bao ma vach

            cv2.rectangle(gray_frame, (x, y), (x + w, y + h), 2)  # Ve hop bao quanh ma vach
            text = "{}".format(barcodeData)
            print(text)
            cv2.putText(gray_frame, text, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            product_id = text
        
        # Gui yeu cau HTTP voi du lieu ma vach va loadcell
        api_url = "http://127.0.0.1:8000/api?id={}&loadcellValue={}".format(product_id, loadcell_value)
        # api_url = "http://192.168.1.190:8000/api?id={}&loadcellValue={}".format(product_id, loadcell_value)
        response = requests.get(api_url)
       
        if product_id is not None:
            GPIO.output(buzzer_pin, GPIO.HIGH)  # Bat buzzer
            time.sleep(0.5)
            GPIO.output(buzzer_pin, GPIO.LOW)  # Tat buzzer
            product_id = None
            time.sleep(3)
        # cv2.imshow("Result", gray_frame)
        
    # Kiem tra trang thai nut bam gui du lieu
    if GPIO.input(button_send_pin) == GPIO.LOW:
        print("da gui")
        GPIO.output(buzzer_pin, GPIO.HIGH)  # Bat buzzer
        time.sleep(0.5)
        GPIO.output(buzzer_pin, GPIO.LOW)  # Tat buzzer
        api_url = "http://127.0.0.1:8000/api?id={}&loadcellValue={}".format(product_id, loadcell_value)
        # api_url = "http://192.168.1.190:8000/api?id={}&loadcellValue={}".format(product_id, loadcell_value)
        response = requests.get(api_url)
        product_id = None
        # Chong doi nut nhan
    time.sleep(0.1)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
