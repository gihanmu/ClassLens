"""Automated headless Chrome CDP screenshot capturer for Gate 4B.2 visual proof."""

import asyncio
import base64
import json
import subprocess
import time
import urllib.request
import websockets
from pathlib import Path

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = Path("docs/screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)


async def run_captures():
    proc = subprocess.Popen(
        [
            CHROME_BIN,
            "--headless=new",
            "--remote-debugging-port=9222",
            "--disable-gpu",
            "--no-sandbox",
            "--user-data-dir=/tmp/chrome_cdp_profile",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)

    try:
        req = urllib.request.Request("http://127.0.0.1:9222/json/new?http://localhost:3000/?tab=dashboard", method="PUT")
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

            # 1. Set Desktop Window 1440x1050
            await send("Emulation.setDeviceMetricsOverride", {
                "width": 1440,
                "height": 1050,
                "deviceScaleFactor": 1,
                "mobile": False,
            })

            # Capture Inspection Modal for Case 3 (Heuristic Confidence Indicator)
            print("Capturing Case 3 Inspection...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=responses&asm=asm_synthetic_cases&response=case_03_ambiguous_incomplete"})
            await asyncio.sleep(3)

            # Scroll the right-hand panel down to expose Critic Audit Card
            await send("Runtime.evaluate", {
                "expression": "document.querySelectorAll('.overflow-y-auto').forEach(el => el.scrollTop = 450);"
            })
            await asyncio.sleep(1)

            res = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate4b2_inspection_heuristic_confidence.png").write_bytes(base64.b64decode(res["data"]))
            print("Saved gate4b2_inspection_heuristic_confidence.png")

            # Capture Case 2 (Persisted Teacher Override & Notes)
            print("Capturing Case 2 Persisted Review...")
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=responses&asm=asm_synthetic_cases&response=case_02_off_by_one_error"})
            await asyncio.sleep(3)

            # Scroll the right-hand panel down to expose Teacher Review Decision & Audit Trail
            await send("Runtime.evaluate", {
                "expression": "document.querySelectorAll('.overflow-y-auto').forEach(el => el.scrollTop = 600);"
            })
            await asyncio.sleep(1)

            res = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate4b2_persistence_after_backend_restart.png").write_bytes(base64.b64decode(res["data"]))
            print("Saved gate4b2_persistence_after_backend_restart.png")

            # Capture Mobile View (iPhone 14 / 390x844) of Student Work
            print("Capturing Mobile View...")
            await send("Emulation.setDeviceMetricsOverride", {
                "width": 390,
                "height": 844,
                "deviceScaleFactor": 2,
                "mobile": True,
            })
            await send("Page.navigate", {"url": "http://localhost:3000/?tab=responses&asm=asm_1065658"})
            await asyncio.sleep(3)

            res = await send("Page.captureScreenshot", {"format": "png"})
            (OUT_DIR / "gate4b2_student_work_mobile.png").write_bytes(base64.b64decode(res["data"]))
            print("Saved gate4b2_student_work_mobile.png")

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    asyncio.run(run_captures())
