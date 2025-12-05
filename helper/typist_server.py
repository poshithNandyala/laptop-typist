# helper/typist_server.py
import time
import random
import threading
import sys
import os

from flask import Flask, request, jsonify, Response
from pynput.keyboard import Controller, Key

# Redirect stdout/stderr to null for pythonw compatibility
if sys.executable.endswith('pythonw.exe'):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

app = Flask(__name__)
keyboard = Controller()

# ---------- CORS: allow calls from any frontend (GitHub Pages, etc.) ----------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# ---------- Runtime config (defaults) ----------
configuredWPM = 100
strictWPM = False
jitterStrengthPct = 12
thinkingSpaceChance = 0
mistakePercent = 3
enableTypos = True
enableLongPauses = True
longPausePercent = 5
longPauseMinMs = 600
longPauseMaxMs = 1200
newlineMode = 1  # 0 keep,1 space,2 remove
extraPunctPause = True

# Code mode (simple)
codeMode = False

# Consecutive mistakes
consecutiveMistakeLimit = 1
consecutiveMistakeCount = 0

# Runtime state
typingActive = False
paused = False
typedChars = 0

# Thread + lock
typing_thread = None
state_lock = threading.Lock()

# ---------- Utilities ----------
def clamp_int(v, a, b):
    return max(a, min(b, v))

def ms_per_char_for_wpm(wpm):
    if wpm < 1:
        wpm = 1
    return 60000.0 / (wpm * 5.0)

def cap_jitter_for_wpm(wpm, jpct):
    if wpm >= 140 and jpct > 0.08:
        return 0.08
    return jpct

def preprocess_text(in_text):
    """
    Non-code mode newline handling:
    newlineMode 0 = keep,
    1 = replace with space,
    2 = remove.
    """
    global newlineMode
    if newlineMode == 0:
        return in_text
    out = []
    for c in in_text:
        if c in ("\r", "\n"):
            if newlineMode == 1:
                out.append(" ")
            # if mode 2 => drop entirely
        else:
            out.append(c)
    return "".join(out)

def coop_sleep(ms):
    """Sleep cooperatively, honoring pause/stop flags."""
    global typingActive, paused
    end = time.time() + ms / 1000.0
    while time.time() < end:
        with state_lock:
            if not typingActive:
                return
            local_paused = paused
        if local_paused:
            # stay paused until unpaused or stopped
            while True:
                time.sleep(0.01)
                with state_lock:
                    if not typingActive or not paused:
                        break
            if not typingActive:
                return
        time.sleep(0.003)

def send_char(c):
    """Simulate typing a character or newline."""
    if c == "\n":
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
    else:
        keyboard.press(c)
        keyboard.release(c)

def send_backspace():
    keyboard.press(Key.backspace)
    keyboard.release(Key.backspace)

# ---------- Typing engine (port of your typeLikeHuman) ----------
def type_like_human(raw_text):
    global typingActive, paused, typedChars, consecutiveMistakeCount

    # snapshot codeMode once (as in your sketch)
    with state_lock:
        local_code_mode = codeMode

    if not raw_text:
        with state_lock:
            typingActive = False
            paused = False
        return

    # Build text based on codeMode
    if not local_code_mode:
        text = preprocess_text(raw_text)
    else:
        # Code mode: strip ALL leading whitespace per line, preserve newlines
        raw = raw_text
        N = len(raw)
        res = []
        start_of_line = True
        i = 0
        while i < N:
            c = raw[i]
            if c == "\r":
                # Normalize CRLF / CR to '\n'
                if i + 1 < N and raw[i+1] == "\n":
                    i += 1
                res.append("\n")
                start_of_line = True
            elif c == "\n":
                res.append("\n")
                start_of_line = True
            else:
                if start_of_line and c.isspace():
                    # drop leading whitespace
                    pass
                else:
                    res.append(c)
                    start_of_line = False
            i += 1
        text = "".join(res)

    N = len(text)
    if N == 0:
        with state_lock:
            typingActive = False
            paused = False
        return

    with state_lock:
        typingActive = True
        paused = False
        typedChars = 0
        consecutiveMistakeCount = 0

    MIN_DELAY = 6.0
    CORR_LIMIT = 0.5
    start_ms = time.time() * 1000.0

    i = 0
    while True:
        with state_lock:
            if not typingActive:
                break
            curWPM = clamp_int(configuredWPM, 1, 300)
            local_jitter = clamp_int(jitterStrengthPct, 5, 45) / 100.0
            local_jitter = cap_jitter_for_wpm(curWPM, local_jitter)
            local_strict = strictWPM
            local_think = thinkingSpaceChance
            local_enableTypos = enableTypos
            local_enableLongPauses = enableLongPauses
            local_longPausePercent = longPausePercent
            local_longPauseMin = longPauseMinMs
            local_longPauseMax = longPauseMaxMs
            local_extraPunctPause = extraPunctPause
            local_mistakePercent = mistakePercent
            local_consLimit = consecutiveMistakeLimit
            local_consCount = consecutiveMistakeCount

        if i >= N:
            break

        c = text[i]

        # Timing calculation (same idea as ESP32 loop)
        now_ms = time.time() * 1000.0
        elapsed = now_ms - start_ms
        base_ms = ms_per_char_for_wpm(curWPM)
        remaining = N - i
        if remaining <= 0:
            remaining = 1
        ideal_elapsed = i * base_ms
        error = elapsed - ideal_elapsed
        correction = -error / remaining
        if correction > base_ms * CORR_LIMIT:
            correction = base_ms * CORR_LIMIT
        if correction < -base_ms * CORR_LIMIT:
            correction = -base_ms * CORR_LIMIT
        next_delay = base_ms + correction
        if next_delay < MIN_DELAY:
            next_delay = MIN_DELAY

        jitter_factor = 1.0 + (random.uniform(-1.0, 1.0) * local_jitter)
        next_delay *= jitter_factor
        if next_delay < MIN_DELAY:
            next_delay = MIN_DELAY

        # In code mode path, we already normalized CRLF to '\n'
        if local_code_mode and c == "\n":
            send_char("\n")
            coop_sleep(next_delay)
            with state_lock:
                typedChars = i + 1
            i += 1
            continue

        is_space = (c == " ")
        is_punct = (c in ".!,?;:")

        # Long pause at spaces
        if (not local_strict and local_enableLongPauses and is_space and
                random.randint(0, 99) < local_longPausePercent):
            coop_sleep(random.randint(local_longPauseMin, local_longPauseMax))

        # Decide typo
        alnum = c.isalnum()
        makeTypo = (not local_strict and local_enableTypos and
                    random.randint(0, 99) < local_mistakePercent and alnum)

        # Respect consecutive mistake limit
        if makeTypo:
            if local_consLimit <= 0 or local_consCount >= local_consLimit:
                makeTypo = False

        if makeTypo:
            # Wrong char, backspace, correct char (same pattern as ESP32)
            wrong_char = chr(ord("a") + random.randint(0, 25))
            if c.isupper():
                wrong_char = wrong_char.upper()

            send_char(wrong_char)
            coop_sleep(max(60, int(next_delay)))
            send_backspace()
            coop_sleep(random.randint(110, 380))
            send_char(c)
            coop_sleep(max(20, min(800, int(next_delay * 0.5) + random.randint(20, 120))))
            with state_lock:
                consecutiveMistakeCount = local_consCount + 1
        else:
            with state_lock:
                consecutiveMistakeCount = 0
            send_char(c)
            extra = 0
            if not local_strict:
                if is_space:
                    extra += random.randint(40, 140)
                if local_extraPunctPause and is_punct:
                    extra += random.randint(80, 220)
                if c in ("\n", "\r"):
                    extra += random.randint(120, 320)
            coop_sleep(next_delay + extra)

        # Thinking pause after spaces
        if (not local_strict and is_space and local_think > 0 and
                random.randint(0, local_think) == 0):
            coop_sleep(random.randint(400, 1000))

        with state_lock:
            typedChars = i + 1

        i += 1

    with state_lock:
        typingActive = False
        paused = False
    # small tail pause
    coop_sleep(120 + random.randint(0, 300))

# ---------- HTTP handlers ----------
@app.route("/")
def root():
    # Optional: local test UI placeholder
    return Response(
        "Laptop Typist helper is running. Use the web UI to control it.",
        mimetype="text/plain"
    )

@app.route("/status")
def handle_status():
    with state_lock:
        s = {
            "ble": True,  # always "connected" in this software version
            "wpm": configuredWPM,
            "strict": strictWPM,
            "jitter": jitterStrengthPct,
            "think": thinkingSpaceChance,
            "typos": enableTypos,
            "lpen": enableLongPauses,
            "nl": newlineMode,
            "codemode": codeMode,
            "typed": int(typedChars),
            "running": typingActive,
            "paused": paused,
            "mistakePct": mistakePercent,
            "cons": consecutiveMistakeLimit,
            "state": "Typing..." if typingActive else "Ready."
        }
    return jsonify(s)

@app.route("/config")
def handle_config():
    global configuredWPM, strictWPM, jitterStrengthPct, thinkingSpaceChance
    global enableTypos, enableLongPauses, longPausePercent
    global longPauseMinMs, longPauseMaxMs, newlineMode, codeMode
    global consecutiveMistakeLimit, mistakePercent

    changed = False
    args = request.args

    with state_lock:
        if "wpm" in args:
            configuredWPM = clamp_int(int(args.get("wpm", 100)), 10, 300); changed = True
        if "strict" in args:
            strictWPM = (int(args.get("strict", 0)) != 0); changed = True
        if "jitter" in args:
            jitterStrengthPct = clamp_int(int(args.get("jitter", 12)), 5, 45); changed = True
        if "think" in args:
            thinkingSpaceChance = clamp_int(int(args.get("think", 0)), 0, 100); changed = True
        if "typos" in args:
            enableTypos = (int(args.get("typos", 1)) != 0); changed = True
        if "lpen" in args:
            enableLongPauses = (int(args.get("lpen", 1)) != 0); changed = True
        if "lpc" in args:
            longPausePercent = clamp_int(int(args.get("lpc", 5)), 0, 100); changed = True
        if "lpmin" in args:
            longPauseMinMs = clamp_int(int(args.get("lpmin", 600)), 50, 20000); changed = True
        if "lpmax" in args:
            longPauseMaxMs = clamp_int(int(args.get("lpmax", 1200)), 50, 30000); changed = True
        if "nl" in args:
            newlineMode = clamp_int(int(args.get("nl", 1)), 0, 2); changed = True
        if "codemode" in args:
            codeMode = (int(args.get("codemode", 0)) != 0); changed = True
        if "cons" in args:
            consecutiveMistakeLimit = clamp_int(int(args.get("cons", 1)), 0, 10); changed = True
        if "mistakePct" in args:
            mistakePercent = clamp_int(int(args.get("mistakePct", 3)), 0, 100); changed = True

        if longPauseMinMs > longPauseMaxMs:
            longPauseMinMs, longPauseMaxMs = longPauseMaxMs, longPauseMinMs

    return (
        "Config updated" if changed else "No changes",
        200 if changed else 400,
        {"Content-Type": "text/plain"}
    )

@app.route("/livewpm")
def handle_livewpm():
    global configuredWPM
    w = request.args.get("wpm")
    if w is None:
        return ("No wpm provided", 400, {"Content-Type": "text/plain"})
    with state_lock:
        configuredWPM = clamp_int(int(w), 1, 200)
        v = configuredWPM
    return (f"Live WPM set to {v}", 200, {"Content-Type": "text/plain"})

@app.route("/type", methods=["POST"])
def handle_type():
    global typingActive, paused, typing_thread
    with state_lock:
        if typingActive:
            return ("Busy: already typing", 409, {"Content-Type": "text/plain"})
    body = request.data.decode("utf-8", errors="ignore")
    if len(body) == 0:
        return ("Empty body", 400, {"Content-Type": "text/plain"})

    # worker thread
    def runner(text):
        try:
            type_like_human(text)
        except Exception as e:
            print("Error in typing thread:", e)
        finally:
            with state_lock:
                typingActive = False
                paused = False

    with state_lock:
        paused = False
        typing_thread = threading.Thread(target=runner, args=(body,), daemon=True)
        typing_thread.start()

    return (f"Typing started ({len(body)} chars)", 200, {"Content-Type": "text/plain"})

@app.route("/stop")
def handle_stop():
    global typingActive, paused
    with state_lock:
        typingActive = False
        paused = False
    return ("Stop requested", 200, {"Content-Type": "text/plain"})

@app.route("/pause")
def handle_pause():
    global paused
    with state_lock:
        if not typingActive:
            return ("Not typing", 409, {"Content-Type": "text/plain"})
        paused = not paused
        p = paused
    return ("Paused" if p else "Resumed", 200, {"Content-Type": "text/plain"})

# ---------- main ----------
if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="0.0.0.0", port=5000, threaded=True)
