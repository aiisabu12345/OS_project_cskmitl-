import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("STRUCTOCR_API_KEY")

API_URL = "https://api.structocr.com/v1/license-plate"


def read_license_plate(image_path):
    if not API_KEY:
        raise Exception("ไม่พบ STRUCTOCR_API_KEY ใน .env")

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    base64_image = base64.b64encode(image_data).decode("utf-8")

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "img": base64_image
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        print("API Error:")
        print(response.status_code)
        print(response.text)
        return None

    result = response.json()

    return result

