#!/usr/bin/env python3
"""Automated browser integration testing and screenshot capture using Chrome DevTools Protocol."""

import asyncio
import base64
import json
import os
import shutil
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR = "/tmp/classlens_cdp_profile"
PORT = 9222
SCREENSHOT_DIR = os.path.join(os.getcwd(), "docs", "screenshots")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
if os.path.exists(PROFILE_DIR):
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)


async def main():
    print(f"Launching Google Chrome in headless mode with remote debugging on port {PORT}...")
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-gpu",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # Wait for Chrome DevTools port to be ready
        ws_url = None
        for _ in range(30):
            try:
                req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1)
                tabs = json.loads(req.read().decode())
                if tabs:
                    ws_url = tabs[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                await asyncio.sleep(0.3)

        if not ws_url:
            raise RuntimeError("Failed to obtain Chrome CDP WebSocket URL")

        print(f"Connected to Chrome CDP at: {ws_url}")

        async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as ws:
            msg_id = 0

            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                current_id = msg_id
                payload = {"id": current_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                while True:
                    resp_raw = await ws.recv()
                    resp = json.loads(resp_raw)
                    if resp.get("id") == current_id:
                        if "error" in resp:
                            raise RuntimeError(f"CDP Error in {method}: {resp['error']}")
                        return resp.get("result", {})

            # Enable necessary domains
            await send("Page.enable")
            await send("DOM.enable")
            await send("Runtime.enable")

            async def set_viewport(width, height, is_mobile=False):
                await send("Emulation.setDeviceMetricsOverride", {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 2,
                    "mobile": is_mobile,
                })

            async def screenshot(filepath):
                res = await send("Page.captureScreenshot", {"format": "png"})
                img_data = base64.b64decode(res["data"])
                with open(filepath, "wb") as f:
                    f.write(img_data)
                print(f"Captured: {filepath} ({len(img_data)} bytes)")

            async def evaluate(expr):
                res = await send("Runtime.evaluate", {
                    "expression": expr,
                    "returnByValue": True,
                    "awaitPromise": True,
                })
                return res.get("result", {}).get("value")

            # -------------------------------------------------------------
            # 1. Desktop Viewport (1440 x 900)
            # -------------------------------------------------------------
            print("\n--- 1. Testing Desktop Workflow (1440x900) ---")
            await set_viewport(1440, 900, is_mobile=False)
            await send("Page.navigate", {"url": "http://127.0.0.1:3000"})
            await asyncio.sleep(2.0)

            # Check if responses are loaded or click Analyze
            print("Triggering batch analysis in dashboard...")
            await evaluate("""
                (async () => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Simulate AI Analysis') || b.innerText.includes('Run Batch Analysis'));
                    if (btn) btn.click();
                })()
            """)
            await asyncio.sleep(2.0)

            # Capture Screen 1: Desktop Dashboard with all 13 responses
            s1_path = os.path.join(SCREENSHOT_DIR, "01_desktop_dashboard_analyzed.png")
            await screenshot(s1_path)

            # -------------------------------------------------------------
            # 2. Inspect Student-06 (resp_80545ef3 - Off-by-one error)
            # -------------------------------------------------------------
            print("\n--- 2. Inspecting Student-06 (resp_80545ef3) Modal ---")
            await evaluate("""
                (() => {
                    // Find card for Student-06 or button with 'Inspect Diagnosis'
                    const cards = Array.from(document.querySelectorAll('div')).filter(d => d.innerText.includes('Student-06'));
                    if (cards.length > 0) {
                        const inspectBtn = cards[0].querySelector('button') || cards[0];
                        inspectBtn.click();
                    } else {
                        const buttons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('Inspect'));
                        if (buttons[5]) buttons[5].click();
                        else if (buttons[0]) buttons[0].click();
                    }
                })()
            """)
            await asyncio.sleep(2.0)

            # Capture Screen 2: Desktop Dual-Pane Modal with Canvas and Diagnosis
            s2_path = os.path.join(SCREENSHOT_DIR, "02_desktop_dual_pane_inspection_modal.png")
            await screenshot(s2_path)

            # -------------------------------------------------------------
            # 3. Open Audit Trail Drawer
            # -------------------------------------------------------------
            print("\n--- 3. Opening Audit Trail Drawer ---")
            await evaluate("""
                (() => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Audit Trail') || b.innerText.includes('History'));
                    if (btn) btn.click();
                })()
            """)
            await asyncio.sleep(1.0)
            s3_path = os.path.join(SCREENSHOT_DIR, "03_desktop_audit_trail.png")
            await screenshot(s3_path)

            # Close modal
            await evaluate("""
                (() => {
                    const closeBtn = document.querySelector('button[aria-label=\"Close modal\"]') || document.querySelector('button[aria-label=\"Close\"]');
                    if (closeBtn) closeBtn.click();
                    else {
                        const btns = Array.from(document.querySelectorAll('button'));
                        const xBtn = btns.find(b => b.innerHTML.includes('lucide-x') || b.innerText === '✕');
                        if (xBtn) xBtn.click();
                    }
                })()
            """)
            await asyncio.sleep(1.0)

            # -------------------------------------------------------------
            # 4. Cohort Intelligence Tab
            # -------------------------------------------------------------
            print("\n--- 4. Viewing Cohort Intelligence Tab ---")
            await evaluate("""
                (() => {
                    const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Cohort Intelligence'));
                    if (tabBtn) tabBtn.click();
                })()
            """)
            await asyncio.sleep(1.5)
            s4_path = os.path.join(SCREENSHOT_DIR, "04_desktop_cohort_intelligence.png")
            await screenshot(s4_path)

            # -------------------------------------------------------------
            # 5. Tablet Viewport (768 x 1024)
            # -------------------------------------------------------------
            print("\n--- 5. Testing Tablet Viewport (768x1024) ---")
            await set_viewport(768, 1024, is_mobile=False)
            # Switch back to Student Responses tab
            await evaluate("""
                (() => {
                    const tabBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Student Responses'));
                    if (tabBtn) tabBtn.click();
                })()
            """)
            await asyncio.sleep(1.0)
            s5_path = os.path.join(SCREENSHOT_DIR, "05_tablet_dashboard.png")
            await screenshot(s5_path)

            # -------------------------------------------------------------
            # 6. Mobile Viewport (390 x 844 - iPhone 14)
            # -------------------------------------------------------------
            print("\n--- 6. Testing Mobile Viewport (390x844) ---")
            await set_viewport(390, 844, is_mobile=True)
            await asyncio.sleep(0.5)

            # Open modal on mobile
            await evaluate("""
                (() => {
                    const buttons = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('Inspect'));
                    if (buttons[5]) buttons[5].click();
                    else if (buttons[0]) buttons[0].click();
                })()
            """)
            await asyncio.sleep(1.5)
            s6_path = os.path.join(SCREENSHOT_DIR, "06_mobile_inspection_modal.png")
            await screenshot(s6_path)

            print("\nBrowser verification and screenshot capture complete!")

    finally:
        print("Stopping Chrome process...")
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()
        if os.path.exists(PROFILE_DIR):
            shutil.rmtree(PROFILE_DIR, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
