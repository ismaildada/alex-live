#!/usr/bin/env python3
"""
ALEX Live Streamer - loader (this is the only file on GitHub).
The real program is downloaded from the license server only while your
device is approved, and runs in memory. WhatsApp: +8801629842299
"""
import json
import os
import subprocess
import sys
import threading
import time
import uuid
import requests  # robust redirect handling

SERVER_URL = "https://script.google.com/macros/s/AKfycbwESAvWYWyvApeBU8h0MUcVlS9nwd7yShirpkse5nokd166fBcOtIHFaCQiDp3M-tfy/exec"
ID_FILE = os.path.expanduser("~/.alex_live_id")
GRACE_SECONDS = 6 * 3600  # keep running this long if internet/server is down
CHECK_EVERY = 300

GREEN, RED, YELLOW, CYAN, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[0m"
last_ok = time.time()


def device_id():
    if os.path.exists(ID_FILE):
        v = open(ID_FILE).read().strip()
        if v:
            return v
    v = uuid.uuid4().hex[:12].upper()
    with open(ID_FILE, "w") as f:
        f.write(v)
    return v


DEVICE_ID = device_id()


def call(action, timeout=30):
    payload = {"action": action, "device_id": DEVICE_ID}
    # requests automatically follows 302 redirects properly
    r = requests.post(SERVER_URL, json=payload, timeout=timeout, allow_redirects=True)
    return r.json()


def license_ok():
    """True while this device is approved."""
    global last_ok
    try:
        r = call("check", 20)
    except Exception:
        return (time.time() - last_ok) < GRACE_SECONDS
    if r.get("status") == "approved":
        last_ok = time.time()
        return True
    return False


def watchdog():
    while True:
        time.sleep(CHECK_EVERY)
        if not license_ok():
            print(RED + "\nSubscription expired or revoked. Stopping." + RESET)
            subprocess.run(["pkill", "-f", "live24/list"])
            os._exit(1)


def main():
    print(CYAN + "\n  ALEX Live Streamer" + RESET)
    print(f"  Your Device ID: {YELLOW}{DEVICE_ID}{RESET}\n")

    shown = None
    while True:
        try:
            r = call("run")
        except Exception as e:
            if shown != "net":
                print(RED + "  Cannot reach server. Check internet, retrying..." + RESET)
                shown = "net"
            time.sleep(15)
            continue
            
        st = r.get("status")
        if st == "approved" and r.get("code"):
            break
            
        if st != shown:
            shown = st
            if st == "pending":
                print(YELLOW + "  Not approved yet." + RESET)
                print("  Send this Device ID to ALEX on WhatsApp: +8801629842299")
                print("  Waiting for approval (checks every 15 seconds)...")
            elif st == "expired":
                print(RED + "  Subscription expired. Contact ALEX on WhatsApp +8801629842299 to renew." + RESET)
            elif st == "blocked":
                print(RED + "  This device is blocked. Contact ALEX." + RESET)
            else:
                print(RED + "  Server error, retrying..." + RESET)
        time.sleep(15)

    print(GREEN + f"  Approved. Valid until: {r.get('expires', '?')}" + RESET)
    time.sleep(1)
    threading.Thread(target=watchdog, daemon=True).start()
    g = {"__name__": "__main__", "__file__": "live24.py", "LICENSE_OK": license_ok}
    exec(compile(r["code"], "live24", "exec"), g)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
