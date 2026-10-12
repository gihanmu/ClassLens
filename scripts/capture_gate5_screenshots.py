"""Automated headless Chrome CDP screenshot capturer for Gate 5 Competition MVP."""

import asyncio
import base64
import json
import io
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from PIL import Image
import websockets

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = Path("docs/screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_uploaded_sample_exists():
    """Uploads a sample worksheet image to asm_1065658 if not already present."""
    # 1. Establish session
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/google",
        data=json.dumps({"demo_mode": True}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        cookies_header = resp.headers.get("Set-Cookie")
        auth_data = json.loads(resp.read().decode())
        csrf_token = auth_data["csrf_token"]

    # 2. Check responses in asm_1065658
    req2 = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/assessments/asm_1065658/responses",
        headers={"Cookie": cookies_header},
    )
    with urllib.request.urlopen(req2) as resp:
        resps = json.loads(resp.read().decode())

    uploaded_id = None
    for r in resps:
        if r.get("source_filename") == "unseen_student_worksheet_demo.png" or "stu_upload_demo" in r.get("pseudonymous_student_id", ""):
            uploaded_id = r["id"]
            break

    if not uploaded_id:
        # Create a sample handwritten number-line style image
        img = Image.new("RGB", (1200, 800), color=(248, 249, 250))
        # Draw some subtle lines
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.line([(100, 400), (1100, 400)], fill=(70, 80, 95), width=3)
        for tick in range(100, 1150, 80):
            draw.line([(tick, 385), (tick, 415)], fill=(70, 80, 95), width=2)
        # Draw sample pencil arc
        draw.arc([200, 250, 600, 400], start=180, end=360, fill=(40, 50, 70), width=3)
        draw.text((220, 220), "+12", fill=(40, 50, 70))
        draw.text((150, 460), "Ans = 2", fill=(20, 20, 40))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        file_bytes = buf.getvalue()

        boundary = "----WebKitFormBoundaryGate5DemoUpload"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="student_id"\r\n\r\n'
            f"stu_upload_demo\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="student_name"\r\n\r\n'
            f"Student-14 (Uploaded Unseen)\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="unseen_student_worksheet_demo.png"\r\n'
            f"Content-Type: image/png\r\n\r\n"
        ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        upload_req = urllib.request.Request(
            "http://127.0.0.1:8000/api/v1/assessments/asm_1065658/upload",
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Cookie": cookies_header,
                "X-CSRF-Token": csrf_token,
                "X-Requested-With": "ClassLens",
            },
        )
        with urllib.request.urlopen(upload_req) as resp:
            upl_data = json.loads(resp.read().decode())
            uploaded_id = upl_data["id"]

    return uploaded_id


async def capture_all():
    uploaded_id = ensure_uploaded_sample_exists()
    print(f"Sample uploaded response ID: {uploaded_id}")

    # Launch Chrome with CDP
    proc = subprocess.Popen(
        [
            CHROME_BIN,
            "--headless=new",
            "--remote-debugging-port=9222",
            "--disable-gpu",
            "--no-sandbox",
            "--user-data-dir=/tmp/chrome_cdp_profile_gate5",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)

    try:
        req = urllib.request.Request(
            "http://127.0.0.1:9222/json/new?http://localhost:3000/?tab=dashboard",
            method="PUT",
        )
        with urllib.request.urlopen(req) as resp:
            target = json.loads(resp.read().decode())
        ws_url = target["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:
            msg_id = 0

            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                while True:
                    raw = await ws.recv()
                    data = json.loads(raw)
                    if data.get("id") == msg_id:
                        return data.get("result", {})

            await send("Page.enable")
            await send("Runtime.enable")

            # Set standard desktop resolution 1440x960
            await send(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": 1440,
                    "height": 960,
                    "deviceScaleFactor": 1,
                    "mobile": False,
                },
            )

            # -------------------------------------------------------------
            # Screenshot 1: Teacher Dashboard End-to-End
            # -------------------------------------------------------------
            print("Capturing Gate 5 Teacher Dashboard...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=dashboard"})
            await asyncio.sleep(2.5)

            shot1 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate5_teacher_dashboard_end_to_end.png").write_bytes(
                base64.b64decode(shot1["data"])
            )
            print("Saved gate5_teacher_dashboard_end_to_end.png")

            # -------------------------------------------------------------
            # Screenshot 2: Assessments Management View
            # -------------------------------------------------------------
            print("Capturing Gate 5 Assessments View...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=assessments"})
            await asyncio.sleep(2.0)

            shot2 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate5_assessment_creation.png").write_bytes(
                base64.b64decode(shot2["data"])
            )
            print("Saved gate5_assessment_creation.png")

            # -------------------------------------------------------------
            # Screenshot 3: Worksheet Upload Modal
            # -------------------------------------------------------------
            print("Capturing Worksheet Upload Modal...")
            # Click the 'Upload Worksheets' button
            await send(
                "Runtime.evaluate",
                {
                    "expression": """
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Upload Worksheets'));
                    if (btn) btn.click();
                    """
                },
            )
            await asyncio.sleep(1.5)

            shot3 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate5_worksheet_upload_modal.png").write_bytes(
                base64.b64decode(shot3["data"])
            )
            print("Saved gate5_worksheet_upload_modal.png")

            # -------------------------------------------------------------
            # Screenshot 4: Student Work View with Uploaded Submission
            # -------------------------------------------------------------
            print("Capturing Student Work View with Uploaded Submission...")
            await send(
                "Page.navigate",
                {"url": "http://localhost:3000/?tab=responses&asm=asm_1065658"},
            )
            await asyncio.sleep(2.5)

            shot4 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate5_uploaded_submission_unassessed.png").write_bytes(
                base64.b64decode(shot4["data"])
            )
            print("Saved gate5_uploaded_submission_unassessed.png")

            # -------------------------------------------------------------
            # Screenshot 5: Dual-Pane Inspection Modal for Uploaded Worksheet
            # -------------------------------------------------------------
            print(f"Capturing Inspection Modal for uploaded worksheet {uploaded_id}...")
            await send(
                "Page.navigate",
                {
                    "url": f"http://localhost:3000/?tab=responses&asm=asm_1065658&response={uploaded_id}"
                },
            )
            await asyncio.sleep(3.0)

            shot5 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate5_inspection_uploaded_worksheet.png").write_bytes(
                base64.b64decode(shot5["data"])
            )
            print("Saved gate5_inspection_uploaded_worksheet.png")

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    asyncio.run(capture_all())
