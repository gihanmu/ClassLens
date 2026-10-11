#!/usr/bin/env python3
"""Capture comprehensive remediation verification screenshots across requested viewports using Chrome CDP."""

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
PROFILE_DIR = "/tmp/classlens_cdp_remediation_profile"
PORT = 9226
SCREENSHOT_DIR = os.path.join(os.getcwd(), "docs", "screenshots")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
if os.path.exists(PROFILE_DIR):
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)


async def main():
    print(f"Launching Google Chrome headless on port {PORT}...")
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-gpu",
        "http://localhost:3000",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        ws_url = None
        for _ in range(40):
            try:
                req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json", timeout=1)
                tabs = json.loads(req.read().decode())
                page_tabs = [t for t in tabs if t.get("type") == "page"]
                if page_tabs:
                    ws_url = page_tabs[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                pass
            await asyncio.sleep(0.2)

        if not ws_url:
            raise RuntimeError("Failed to obtain Chrome CDP Page WebSocket URL")

        print(f"Connected to Chrome CDP page target at: {ws_url}")

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
                print(f"Captured: {os.path.basename(filepath)} ({len(img_data)} bytes)")

            async def evaluate(expr):
                res = await send("Runtime.evaluate", {
                    "expression": expr,
                    "returnByValue": True,
                    "awaitPromise": True,
                })
                return res.get("result", {}).get("value")

            # Wait for data load
            await asyncio.sleep(2.0)

            # -------------------------------------------------------------
            # 1. 1440px Standard Desktop (Initial Visit with Welcome Hero)
            # -------------------------------------------------------------
            print("\n--- 1. Desktop 1440x900 (Initial Visit with Welcome Hero) ---")
            await set_viewport(1440, 900, is_mobile=False)
            await asyncio.sleep(1.0)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_1440px_desktop.png"))

            # Scroll to cards detail
            await evaluate("window.scrollTo({ top: 400, behavior: 'instant' });")
            await asyncio.sleep(0.5)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_cards_detail.png"))

            # -------------------------------------------------------------
            # 2. Dismiss Welcome Banner (Returning User Experience)
            # -------------------------------------------------------------
            print("\n--- 2. Testing Welcome Banner Dismissal (Returning User) ---")
            await evaluate("""
                (() => {
                    window.scrollTo({ top: 0, behavior: 'instant' });
                    // Click Dismiss / Hide Introduction
                    const dismissBtn = Array.from(document.querySelectorAll('button')).find(
                        b => b.innerText.includes('Hide Introduction') || b.innerText.includes('Dismiss') || b.getAttribute('aria-label') === 'Dismiss banner'
                    );
                    if (dismissBtn) dismissBtn.click();
                })()
            """)
            await asyncio.sleep(1.0)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_returning_user_dashboard.png"))

            # -------------------------------------------------------------
            # 3. 1280px Desktop
            # -------------------------------------------------------------
            print("\n--- 3. Desktop 1280x800 ---")
            await set_viewport(1280, 800, is_mobile=False)
            await asyncio.sleep(0.8)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_1280px_desktop.png"))

            # -------------------------------------------------------------
            # 4. 1024px Small Desktop
            # -------------------------------------------------------------
            print("\n--- 4. Desktop 1024x768 ---")
            await set_viewport(1024, 768, is_mobile=False)
            await asyncio.sleep(0.8)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_1024px_desktop.png"))

            # -------------------------------------------------------------
            # 5. 768px Tablet Viewport (Clean 2-column grid, no title wrapping)
            # -------------------------------------------------------------
            print("\n--- 5. Tablet 768x1024 ---")
            await set_viewport(768, 1024, is_mobile=False)
            await evaluate("window.scrollTo({ top: 0, behavior: 'instant' });")
            await asyncio.sleep(0.8)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_768px_tablet.png"))

            # -------------------------------------------------------------
            # 6. 390px Mobile Viewport (iPhone 14, 1-column grid, 44px tap targets)
            # -------------------------------------------------------------
            print("\n--- 6. Mobile 390x844 ---")
            await set_viewport(390, 844, is_mobile=True)
            await evaluate("window.scrollTo({ top: 0, behavior: 'instant' });")
            await asyncio.sleep(0.8)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_390px_mobile.png"))

            # -------------------------------------------------------------
            # 7. 1920px Ultra-Wide Desktop (4-column grid check)
            # -------------------------------------------------------------
            print("\n--- 7. Wide Desktop 1920x1080 ---")
            await set_viewport(1920, 1080, is_mobile=False)
            await evaluate("window.scrollTo({ top: 0, behavior: 'instant' });")
            await asyncio.sleep(0.8)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_1920px_wide.png"))

            # -------------------------------------------------------------
            # 8. Inspection Modal (Student-06 Dual-Pane)
            # -------------------------------------------------------------
            print("\n--- 8. Inspection Modal (Student-06 at 1440x900) ---")
            await set_viewport(1440, 900, is_mobile=False)
            await evaluate("""
                (() => {
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
            await asyncio.sleep(1.5)
            await screenshot(os.path.join(SCREENSHOT_DIR, "remediation_inspection_modal.png"))

            print("\nAll remediation screenshots captured successfully!")

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            chrome_proc.kill()
        if os.path.exists(PROFILE_DIR):
            shutil.rmtree(PROFILE_DIR, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
