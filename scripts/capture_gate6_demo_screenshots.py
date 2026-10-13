"""Automated headless Chrome CDP screenshot capturer for Gate 6 Controlled Competition Demo.

Captures all 7 required competition acceptance screenshots:
1. demo_01_landing.png: Competition demo landing page / Teacher dashboard.
2. demo_02_upload.png: Worksheet upload workflow.
3. demo_03_awaiting_auth.png: Analysis trigger / fail-closed authorization state.
4. demo_04_evidence_inspection.png: Evidence inspection with number line geometry and SymPy.
5. demo_05_teacher_review.png: Teacher review interface with Independent Critic findings.
6. demo_06_cohort_insights.png: Cohort insights with misconception distribution.
7. demo_07_evaluation_lab.png: AI Reliability Lab with offline suite and live evaluation tab.
"""

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


def ensure_demo_data_ready():
    """Initializes session and ensures demo assessments and uploaded worksheet exist."""
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/google",
        data=json.dumps({"demo_mode": True}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        cookies_header = resp.headers.get("Set-Cookie")
        auth_data = json.loads(resp.read().decode())
        csrf_token = auth_data["csrf_token"]

    # Trigger analysis for demo responses if not already analyzed
    analyze_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/assessments/asm_1065658/analyze",
        data=json.dumps({}).encode(),
        headers={
            "Content-Type": "application/json",
            "Cookie": cookies_header,
            "X-CSRF-Token": csrf_token,
            "X-Requested-With": "ClassLens",
        },
    )
    try:
        with urllib.request.urlopen(analyze_req) as resp:
            pass
    except Exception as e:
        print(f"Analysis trigger note: {e}")

    return cookies_header


async def capture_all_screenshots():
    cookies_header = ensure_demo_data_ready()

    proc = subprocess.Popen(
        [
            CHROME_BIN,
            "--headless=new",
            "--remote-debugging-port=9223",
            "--disable-gpu",
            "--no-sandbox",
            "--no-first-run",
            "--no-default-browser-check",
            "--user-data-dir=/tmp/chrome_cdp_profile_gate6",
            "http://localhost:3000",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        ws_url = None
        for _ in range(40):
            try:
                req = urllib.request.urlopen("http://127.0.0.1:9223/json", timeout=1)
                tabs = json.loads(req.read().decode())
                page_tabs = [t for t in tabs if t.get("type") == "page"]
                if page_tabs:
                    ws_url = page_tabs[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                pass
            await asyncio.sleep(0.3)

        if not ws_url:
            raise RuntimeError("Failed to obtain Chrome CDP Page WebSocket URL")

        print(f"Connected to Chrome CDP page target: {ws_url}")

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

            # Standard desktop resolution 1440x960
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
            # Screenshot 1: demo_01_landing.png
            # -------------------------------------------------------------
            print("1. Capturing demo_01_landing.png...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=dashboard"})
            await asyncio.sleep(2.5)
            shot1 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "demo_01_landing.png").write_bytes(base64.b64decode(shot1["data"]))
            print(" -> Saved demo_01_landing.png")

            # -------------------------------------------------------------
            # Screenshot 2: demo_02_upload.png
            # -------------------------------------------------------------
            print("2. Capturing demo_02_upload.png...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=assessments"})
            await asyncio.sleep(2.0)
            # Open upload modal
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
            shot2 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "demo_02_upload.png").write_bytes(base64.b64decode(shot2["data"]))
            print(" -> Saved demo_02_upload.png")

            # -------------------------------------------------------------
            # Screenshot 3: demo_03_awaiting_auth.png
            # -------------------------------------------------------------
            print("3. Capturing demo_03_awaiting_auth.png...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=responses&asm=asm_1065658"})
            await asyncio.sleep(2.5)
            shot3 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "demo_03_awaiting_auth.png").write_bytes(base64.b64decode(shot3["data"]))
            print(" -> Saved demo_03_awaiting_auth.png")

            # -------------------------------------------------------------
            # Screenshot 4: demo_04_evidence_inspection.png
            # -------------------------------------------------------------
            print("4. Capturing demo_04_evidence_inspection.png...")
            await send(
                "Page.navigate",
                {"url": "http://localhost:3000/?tab=responses&asm=asm_1065658&response=asm_1065658_resp_001"},
            )
            await asyncio.sleep(3.0)
            shot4 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "demo_04_evidence_inspection.png").write_bytes(base64.b64decode(shot4["data"]))
            print(" -> Saved demo_04_evidence_inspection.png")

            # -------------------------------------------------------------
            # Screenshot 5: demo_05_teacher_review.png
            # -------------------------------------------------------------
            print("5. Capturing demo_05_teacher_review.png...")
            # Scroll to review section or open review tab in modal
            await send(
                "Runtime.evaluate",
                {
                    "expression": """
                    const modal = document.querySelector('[role="dialog"]') || document.body;
                    const reviewBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('Review') || b.textContent.includes('Audit'));
                    if (reviewBtn) reviewBtn.click();
                    """
                },
            )
            await asyncio.sleep(1.5)
            shot5 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "demo_05_teacher_review.png").write_bytes(base64.b64decode(shot5["data"]))
            print(" -> Saved demo_05_teacher_review.png")

            # -------------------------------------------------------------
            # Screenshot 6: demo_06_cohort_insights.png
            # -------------------------------------------------------------
            print("6. Capturing demo_06_cohort_insights.png...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=insights&asm=asm_1065658"})
            await asyncio.sleep(2.5)
            shot6 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "demo_06_cohort_insights.png").write_bytes(base64.b64decode(shot6["data"]))
            print(" -> Saved demo_06_cohort_insights.png")

            # -------------------------------------------------------------
            # Screenshot 7: demo_07_evaluation_lab.png
            # -------------------------------------------------------------
            print("7. Capturing demo_07_evaluation_lab.png...")
            await send("Page.navigate", {"url": "http://localhost:3000/dev/evaluation"})
            await asyncio.sleep(2.5)
            # Click the 'Authorized Live Handwriting Evaluation' tab to showcase the not-performed state
            await send(
                "Runtime.evaluate",
                {
                    "expression": """
                    const liveTab = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Authorized Live'));
                    if (liveTab) liveTab.click();
                    """
                },
            )
            await asyncio.sleep(1.5)
            shot7 = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "demo_07_evaluation_lab.png").write_bytes(base64.b64decode(shot7["data"]))
            print(" -> Saved demo_07_evaluation_lab.png")

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    asyncio.run(capture_all_screenshots())
