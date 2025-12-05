# helper/typist_server.py
import time
import random
import threading
import statistics
import json

from flask import Flask, request, jsonify, Response
from pynput.keyboard import Controller, Key

app = Flask(__name__)
keyboard = Controller()

# ---------- CORS ----------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# ---------- User's Typing Profile ----------
class TypingProfile:
    def __init__(self):
        self.calibrated = False
        self.base_wpm = 60  # WPM detected during calibration
        
        # Raw captured data
        self.hold_times = []      # Key hold durations
        self.flight_times = []    # Time between keys
        self.digraph_times = {}   # "ab" -> [times]
        
        # Computed stats
        self.hold_mean = 85
        self.hold_std = 25
        self.flight_mean = 150
        self.flight_std = 50
        
        # Character-specific delays (relative to mean)
        self.char_factors = {}    # 'a' -> 0.9 means 10% faster
        
    def compute_stats(self):
        if len(self.hold_times) > 5:
            self.hold_mean = statistics.mean(self.hold_times)
            self.hold_std = statistics.stdev(self.hold_times) if len(self.hold_times) > 1 else self.hold_mean * 0.3
        
        if len(self.flight_times) > 5:
            self.flight_mean = statistics.mean(self.flight_times)
            self.flight_std = statistics.stdev(self.flight_times) if len(self.flight_times) > 1 else self.flight_mean * 0.35
            # Estimate base WPM from flight time
            # Average 5 chars per word, so WPM = 60000 / (flight_mean * 5)
            self.base_wpm = 60000 / (self.flight_mean * 5)
        
        # Compute digraph means
        for digraph, times in self.digraph_times.items():
            if len(times) >= 2:
                self.digraph_times[digraph] = statistics.mean(times)
            elif len(times) == 1:
                self.digraph_times[digraph] = times[0]
    
    def get_hold_time(self, target_wpm):
        """Get a hold time scaled to target WPM."""
        scale = self.base_wpm / max(target_wpm, 10)
        base = random.gauss(self.hold_mean, self.hold_std)
        scaled = base * scale
        return max(20, min(300, scaled))
    
    def get_flight_time(self, prev_char, curr_char, target_wpm):
        """Get flight time between two characters, scaled to target WPM."""
        scale = self.base_wpm / max(target_wpm, 10)
        
        # Check for digraph-specific timing
        digraph = (prev_char + curr_char).lower()
        if digraph in self.digraph_times and isinstance(self.digraph_times[digraph], (int, float)):
            base = self.digraph_times[digraph]
            # Add small variation
            base = random.gauss(base, base * 0.15)
        else:
            base = random.gauss(self.flight_mean, self.flight_std)
        
        scaled = base * scale
        return max(15, min(1000, scaled))
    
    def get_space_pause(self, target_wpm):
        """Pause after space - slightly longer."""
        scale = self.base_wpm / max(target_wpm, 10)
        base = self.flight_mean * 1.4
        return max(30, random.gauss(base, base * 0.3) * scale)
    
    def get_punct_pause(self, target_wpm):
        """Pause after punctuation - longer."""
        scale = self.base_wpm / max(target_wpm, 10)
        base = self.flight_mean * 2.2
        return max(50, random.gauss(base, base * 0.3) * scale)

profile = TypingProfile()

# ---------- Runtime Settings ----------
target_wpm = 80
enable_typos = True
typo_percent = 2
newline_mode = 1  # 0=keep, 1=space, 2=remove
code_mode = False

# Runtime state
typing_active = False
is_paused = False
typed_count = 0
typing_thread = None
lock = threading.Lock()

# ---------- Keyboard Helpers ----------
NEARBY_KEYS = {
    'q': 'was', 'w': 'qesa', 'e': 'wrds', 'r': 'etfd', 't': 'ryfg',
    'y': 'tuhg', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'awedxz', 'd': 'serfcx', 'f': 'drtgvc',
    'g': 'ftyhbv', 'h': 'gyujnb', 'j': 'huikmn', 'k': 'jiolm',
    'l': 'kop', 'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb',
    'b': 'vghn', 'n': 'bhjm', 'm': 'njk'
}

def get_nearby_key(c):
    c_lower = c.lower()
    if c_lower in NEARBY_KEYS:
        return random.choice(NEARBY_KEYS[c_lower])
    return chr(ord('a') + random.randint(0, 25))

def press_key(c, hold_ms):
    """Press and release a key with given hold time."""
    try:
        if c == '\n':
            keyboard.press(Key.enter)
            time.sleep(hold_ms / 1000)
            keyboard.release(Key.enter)
        else:
            keyboard.press(c)
            time.sleep(hold_ms / 1000)
            keyboard.release(c)
    except:
        pass

def press_backspace(hold_ms):
    keyboard.press(Key.backspace)
    time.sleep(hold_ms / 1000)
    keyboard.release(Key.backspace)

def sleep_check(ms):
    """Sleep while checking for stop/pause."""
    global typing_active, is_paused
    end_time = time.time() + ms / 1000
    
    while time.time() < end_time:
        with lock:
            if not typing_active:
                return False
            if is_paused:
                # Wait while paused
                while is_paused and typing_active:
                    time.sleep(0.05)
                with lock:
                    if not typing_active:
                        return False
        time.sleep(0.005)
    return True

# ---------- Main Typing Function ----------
def type_text(text):
    global typing_active, is_paused, typed_count, profile, target_wpm
    
    if not text:
        return
    
    # Preprocess based on mode
    if code_mode:
        # Strip leading whitespace per line, keep newlines
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        text = '\n'.join(line.lstrip() for line in lines)
    elif newline_mode == 1:
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    elif newline_mode == 2:
        text = text.replace('\r\n', '').replace('\n', '').replace('\r', '')
    
    with lock:
        typing_active = True
        is_paused = False
        typed_count = 0
        current_wpm = target_wpm
    
    prev_char = ''
    consecutive_typos = 0
    
    for i, char in enumerate(text):
        with lock:
            if not typing_active:
                break
            current_wpm = target_wpm  # Get latest WPM
        
        # Calculate timing using profile
        if profile.calibrated:
            hold_time = profile.get_hold_time(current_wpm)
            
            if char == ' ':
                flight_time = profile.get_space_pause(current_wpm)
            elif char in '.!?,;:':
                flight_time = profile.get_punct_pause(current_wpm)
            elif char == '\n':
                flight_time = profile.get_punct_pause(current_wpm) * 1.5
            else:
                flight_time = profile.get_flight_time(prev_char, char, current_wpm)
        else:
            # Default timing based on WPM
            ms_per_char = 60000 / (current_wpm * 5)
            hold_time = random.gauss(80, 20)
            flight_time = ms_per_char + random.gauss(0, ms_per_char * 0.2)
            
            if char == ' ':
                flight_time *= 1.3
            elif char in '.!?,;:':
                flight_time *= 2.0
        
        # Wait before typing
        if not sleep_check(flight_time):
            break
        
        # Decide if making a typo
        make_typo = False
        if enable_typos and char.isalpha() and consecutive_typos < 1:
            if random.random() * 100 < typo_percent:
                make_typo = True
        
        if make_typo:
            # Type wrong key
            wrong = get_nearby_key(char)
            if char.isupper():
                wrong = wrong.upper()
            press_key(wrong, hold_time)
            
            # Notice delay
            if not sleep_check(random.uniform(120, 280)):
                break
            
            # Backspace
            press_backspace(random.uniform(50, 90))
            
            # Correction delay
            if not sleep_check(random.uniform(80, 200)):
                break
            
            # Correct key
            press_key(char, hold_time)
            consecutive_typos += 1
        else:
            press_key(char, hold_time)
            consecutive_typos = 0
        
        prev_char = char
        with lock:
            typed_count = i + 1
    
    with lock:
        typing_active = False
        is_paused = False

# ---------- HTTP Endpoints ----------
@app.route("/")
def index():
    return "Laptop Typist Helper Running. Open the Web UI to control."

@app.route("/status")
def status():
    with lock:
        return jsonify({
            "running": typing_active,
            "paused": is_paused,
            "typed": typed_count,
            "wpm": target_wpm,
            "calibrated": profile.calibrated,
            "baseWpm": round(profile.base_wpm, 1) if profile.calibrated else None,
            "typos": enable_typos,
            "typoPct": typo_percent,
            "newlineMode": newline_mode,
            "codeMode": code_mode
        })

@app.route("/setwpm")
def set_wpm():
    global target_wpm
    wpm = request.args.get("wpm", type=int)
    if wpm is None:
        return "Missing wpm", 400
    with lock:
        target_wpm = max(10, min(300, wpm))
    return f"WPM set to {target_wpm}"

@app.route("/config")
def config():
    global target_wpm, enable_typos, typo_percent, newline_mode, code_mode
    
    args = request.args
    with lock:
        if "wpm" in args:
            target_wpm = max(10, min(300, int(args["wpm"])))
        if "typos" in args:
            enable_typos = args["typos"] == "1"
        if "typoPct" in args:
            typo_percent = max(0, min(20, int(args["typoPct"])))
        if "nl" in args:
            newline_mode = max(0, min(2, int(args["nl"])))
        if "codemode" in args:
            code_mode = args["codemode"] == "1"
    
    return "OK"

@app.route("/calibrate", methods=["POST", "OPTIONS"])
def calibrate():
    global profile
    
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.get_json()
        if not data:
            return "No data", 400
        
        hold_times = data.get("holdTimes", [])
        flight_times = data.get("flightTimes", [])
        digraphs = data.get("digraphs", {})
        
        if len(hold_times) < 10 or len(flight_times) < 10:
            return "Need more typing data (at least 20 characters)", 400
        
        with lock:
            profile.hold_times = hold_times
            profile.flight_times = flight_times
            profile.digraph_times = digraphs
            profile.compute_stats()
            profile.calibrated = True
        
        return jsonify({
            "success": True,
            "baseWpm": round(profile.base_wpm, 1),
            "holdMean": round(profile.hold_mean, 1),
            "flightMean": round(profile.flight_mean, 1),
            "digraphs": len([d for d in profile.digraph_times if isinstance(profile.digraph_times[d], (int, float))])
        })
    
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/type", methods=["POST"])
def type_endpoint():
    global typing_thread, typing_active
    
    with lock:
        if typing_active:
            return "Already typing", 409
    
    text = request.data.decode("utf-8", errors="ignore")
    if not text:
        return "Empty text", 400
    
    def worker():
        try:
            type_text(text)
        except Exception as e:
            print(f"Typing error: {e}")
        finally:
            with lock:
                typing_active = False
    
    typing_thread = threading.Thread(target=worker, daemon=True)
    typing_thread.start()
    
    return f"Started typing {len(text)} chars"

@app.route("/stop")
def stop():
    global typing_active, is_paused
    with lock:
        typing_active = False
        is_paused = False
    return "Stopped"

@app.route("/pause")
def pause():
    global is_paused
    with lock:
        if not typing_active:
            return "Not typing", 400
        is_paused = not is_paused
        return "Paused" if is_paused else "Resumed"

# ---------- Main ----------
if __name__ == "__main__":
    print("=" * 50)
    print("  LAPTOP TYPIST - Human-like Typing")
    print("=" * 50)
    print("Server: http://0.0.0.0:5000")
    print()
    print("1. Open Web UI and calibrate your typing")
    print("2. Set your desired WPM")
    print("3. Paste text and click Type!")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, threaded=True)
