from ocr import read_license_plate


IMAGE_PATH = "unnamed.png"


def main():

    print("================================")
    print("     Thai License Plate OCR")
    print("================================")

    print(f"กำลังอ่านรูป: {IMAGE_PATH}")

    result = read_license_plate(IMAGE_PATH)

    if result is None:
        print("อ่านทะเบียนไม่สำเร็จ")
        return

    # ดู Response ทั้งหมดก่อน
    print("\nAPI Response:")
    print(result)

    # ตรวจสอบ success
    if not result.get("success"):
        print("\nOCR ไม่สำเร็จ")
        return

    data = result.get("data", {})

    plates = data.get("plates", [])

    if len(plates) == 0:
        print("\nไม่พบทะเบียนรถ")
        return

    print("\n========== RESULT ==========")

    for i, plate in enumerate(plates):

        print(f"\nรถคันที่ {i + 1}")

        print(
            "ทะเบียน:",
            plate.get("plate_number")
        )

        print(
            "ทะเบียนแบบ normalized:",
            plate.get("plate_number_normalized")
        )

        print(
            "สีป้าย:",
            plate.get("plate_color")
        )

        print(
            "ประเภท:",
            plate.get("plate_type")
        )

    print("\nจังหวัด/พื้นที่:")
    print(data.get("region_text"))

    print("\nประเทศ:")
    print(data.get("country_guess"))

    print("\nความมั่นใจ:")
    print(data.get("confidence_score"))


if __name__ == "__main__":
    main()