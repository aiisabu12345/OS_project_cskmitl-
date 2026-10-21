from pathlib import Path
import time

import streamlit as st

from ocr import read_license_plate

BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
REFRESH_SECONDS = 2

st.set_page_config(page_title="Thai License Plate OCR", page_icon="🚗", layout="centered")

st.markdown(
    """
    <style>
    .plate-box {
        background: #fff;
        color: #111;
        border: 4px solid #222;
        border-radius: 14px;
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        padding: 4px 10px;
        margin: 4px 0 10px 0;
        letter-spacing: 2px;
    }
    .sub { color: #888; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Thai License Plate OCR")
st.caption(f"ระบบจะอ่านรูปให้อัตโนมัติ")


def latest_image():
    files = [p for p in IMAGES_DIR.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def file_signature(path: Path):
    stat = path.stat()
    return (path.name, stat.st_mtime_ns, stat.st_size)


def run_ocr(path: Path):
    try:
        result = read_license_plate(str(path))
        if result is None:
            return {"error": "เรียก API ไม่สำเร็จ (ดูรายละเอียดใน Terminal)"}
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


def show_result(path: Path, outcome: dict):
    st.image(str(path), caption=path.name, use_container_width=True)

    if "error" in outcome:
        st.error(outcome["error"])
        return

    result = outcome["result"]
    if not result.get("success"):
        st.error("OCR ไม่สำเร็จ")
        with st.expander("ดู API Response"):
            st.json(result)
        return

    data = result.get("data", {}) or {}
    plates = data.get("plates", []) or []

    if not plates:
        st.warning("ไม่พบทะเบียนรถในรูปนี้")
        return

    for i, plate in enumerate(plates, start=1):
        if len(plates) > 1:
            st.subheader(f"รถคันที่ {i}")
        st.markdown(
            f"<div class='plate-box'>{plate.get('plate_number') or '-'}</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("สีป้าย", plate.get("plate_color") or "-")
        c2.metric("ประเภท", plate.get("plate_type") or "-")
        c3.metric("Normalized", plate.get("plate_number_normalized") or "-")

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("จังหวัด/พื้นที่", data.get("region_text") or "-")
    c2.metric("ประเทศ", data.get("country_guess") or "-")
    conf = data.get("confidence_score")
    c3.metric("ความมั่นใจ", f"{conf:.0%}" if isinstance(conf, (int, float)) and conf <= 1 else (conf or "-"))

    with st.expander("ดู API Response ทั้งหมด"):
        st.json(result)


@st.fragment(run_every=REFRESH_SECONDS)
def watcher():
    path = latest_image()

    if path is None:
        st.session_state.pop("signature", None)
        st.session_state.pop("outcome", None)
        st.info("📭 ไม่พบรูปภาพ — กำลังรอรูปภาพ...")
        return

    # รูปเพิ่งถูกวาง/ยังคัดลอกไม่เสร็จ ให้รอรอบถัดไป
    if time.time() - path.stat().st_mtime < 1:
        st.info("⏳ กำลังรับไฟล์...")
        return

    sig = file_signature(path)

    if st.session_state.get("signature") != sig:
        with st.spinner(f"กำลังอ่านรูป {path.name} ..."):
            st.session_state["outcome"] = run_ocr(path)
        st.session_state["signature"] = sig

    show_result(path, st.session_state["outcome"])

    if "error" in st.session_state["outcome"]:
        if st.button("🔄 ลองอ่านใหม่"):
            st.session_state.pop("signature", None)
            st.rerun(scope="fragment")


watcher()