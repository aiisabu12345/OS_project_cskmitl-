from ocr import read_license_plate_frame
from gpiozero import Button, LED
from pathlib import Path
from numbers import Real
from threading import Lock
import time
import cv2
from signal import pause

# === CONFIG ====
CONFIDENCE_THRESHOLD = 0.5
BUTTON_GPIO = 2
CAR_LIST_PATH = Path(__file__).with_name("CarList.txt")
green_led = LED(17)
red_led = LED(27)
processing_lock = Lock()

# === INIT ===
def normalize_text(value):
    return "".join(str(value).split()).upper()

with open("./CarList.txt",encoding="utf-8") as f:
    car_list = [normalize_text(line) for line in f if line.strip()]

# === UTILS ===
def pi_capture():
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        raise RuntimeError("เปิดกล้องไม่ได้")

    try:
        time.sleep(2)
        ret,frame = cam.read()

        if not ret:
            raise RuntimeError("กล้องจับภาพไม่ได้")

        return frame
    finally:
        cam.release()

# === MAIN WORKFLOW ===
def set_leds(green=False, red=False):
    green_led.value = green
    red_led.value = red


def deny_access(message):
    set_leds(red=True)
    print(message)


def on_button_pressed():
    if not processing_lock.acquire(blocking=False):
        print("กำลังประมวลผลอยู่ กรุณารอ")
        return

    try:
        set_leds()
        print("Capturing image...")
        img = pi_capture()
        if img is None:
            deny_access("ไม่ได้ภาพจากกล้อง")
            return

        print("================================")
        print("     Thai License Plate OCR")
        print("================================")
        result = read_license_plate_frame(img)

        if not result or not result.get("success"):
            deny_access("\nOCR ไม่สำเร็จ")
            return

        data = result.get("data") or {}
        plates = data.get("plates") or []
        if not plates or not isinstance(plates[0], dict):
            deny_access("\nไม่พบทะเบียนรถ")
            return

        confidence = data.get("confidence_score")
        if (
            not isinstance(confidence, Real)
            or confidence < CONFIDENCE_THRESHOLD
        ):
            deny_access("\nความแม่นยำไม่เพียงพอ")
            return

        plate = plates[0]
        values = (
            plate.get("plate_number_normalized"),
            plate.get("plate_color"),
            data.get("region_text"),
        )
        if not all(isinstance(value, str) and value.strip() for value in values):
            deny_access("\nข้อมูลทะเบียนไม่ครบ")
            return

        plate_key = tuple(normalize_text(value) for value in values)
        plate_text = "".join(plate_key)
        print(f"ทะเบียน: {plate_key[0]}, สีป้าย: {plate_key[1]}, จังหวัด: {plate_key[2]}")
        print(f"ความแม่นยำ: {confidence:.2f}")

        if plate_text in car_list:
            set_leds(green=True)
            print("\nอนุญาตให้ผ่าน")
        else:
            deny_access("\nไม่อนุญาตให้ผ่าน")
    except Exception as error:
        deny_access(f"\nเกิดข้อผิดพลาด: {error}")
    finally:
        processing_lock.release()

def main():
    set_leds()
    button = Button(BUTTON_GPIO, bounce_time=0.2)
    button.when_pressed = on_button_pressed

    pause()

if __name__ == "__main__":
    main()
