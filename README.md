# ⌨️ Laptop Typist

**Make your computer type like a human!**

Laptop Typist automatically types text for you — with realistic speed, natural pauses, and even occasional typos that get corrected. It looks exactly like a real person is typing.

---

## 🎯 What Can You Use This For?

- **Demonstrations** — Show live coding or writing without actually typing
- **Presentations** — Auto-type code examples while you explain
- **Content Creation** — Create realistic typing videos
- **Accessibility** — Type long text without strain

---

## 📋 What You Need (Prerequisites)

### 1. Install Python

Python is a programming language that runs this tool.

1. Go to **[python.org/downloads](https://www.python.org/downloads/)**
2. Click the big **"Download Python"** button
3. Run the installer
4. ⚠️ **IMPORTANT:** Check the box that says **"Add Python to PATH"**
5. Click "Install Now"

**To verify it worked:** Open Command Prompt (search "cmd" in Start menu) and type:
```
python --version
```
You should see something like `Python 3.11.5`

### 2. Install Required Packages

Open Command Prompt and run these two commands (copy-paste each line and press Enter):

```
pip install flask
```
```
pip install pynput
```

---

## 🚀 How to Use

> **You need TWO laptops on the same WiFi:**
> - 🎯 **Target Laptop** — The one that will TYPE
> - 🎮 **Control Laptop** — The one YOU use to send text

---

### Step 1: Download on Target Laptop

On the **Target Laptop** (where typing will happen):

**Option A — Download ZIP (Easiest):**
1. Click the green **"Code"** button above
2. Click **"Download ZIP"**
3. Extract the folder to your computer

**Option B — Fork (If you want your own copy on GitHub):**
1. Click the **"Fork"** button in the top-right corner
2. This creates your own copy of the project
3. Then download or clone from your forked repo

---

### Step 2: Setup Target Laptop (One-Time)

**2.1 — Find the IP Address:**
- Open **Command Prompt** (search "cmd" in Start menu)
- Type `ipconfig` and press Enter
- Find **IPv4 Address** (example: `192.168.1.50`)
- **Write this down!**

**2.2 — Allow Firewall (one-time):**
- Search **"Windows Defender Firewall"** in Start menu
- Click **"Allow an app through firewall"**
- Click **"Change settings"** → **"Allow another app"**
- Add `python.exe` and check both **Private** and **Public**

**2.3 — Start the program:**
- Open the `laptop-typist` folder
- **Double-click `start.vbs`** (runs silently in background — no windows!)
- The servers start automatically in the background

---

### Step 3: Control from Your Laptop

On the **Control Laptop** (where YOU sit):

1. Open your browser (Chrome, Edge, Firefox)
2. Go to: `http://<TARGET_IP>:8000`  
   Example: If the target laptop IPv4 address is **192.168.1.50**, then use:  
   `http://192.168.1.50:8000`
3. Set **Helper URL** to: `http://<TARGET_IP>:5000`  
   Example: If the target laptop IPv4 address is **192.168.1.50**, then use:  
   `http://192.168.1.50:5000`

**Replace `<TARGET_IP>` with your target laptop's IPv4 address.**

---

### Step 4: Start Typing!

1. **Paste your text** in the big text box on Control Laptop
2. **Go to Target Laptop** — click where you want text to appear (Word, Notepad, etc.)
3. **Go back to Control Laptop** — click **"Type on target"**
4. Watch the Target Laptop type! ✨

---

### Step 5: Stop the Program

On the **Target Laptop**:
- **Double-click `stop.vbs`** (runs silently — stops all background servers)

---

## 🎮 Control Panel Guide

![Control Panel Layout](https://via.placeholder.com/800x400?text=Control+Panel+Screenshot)

| Button | What It Does |
|--------|--------------|
| **Type on target** | Starts typing your text |
| **Apply settings** | Saves your speed/behavior changes |
| **Status** | Shows if it's running |
| **STOP** | Immediately stops typing |
| **Play/Pause** | Pause and resume typing |

---

## ⚙️ Settings Explained

| Setting            | What It Means                                   | Recommended                         |
|--------------------|--------------------------------------------------|-------------------------------------|
| **WPM**            | Words Per Minute — how fast it types             | 80–120 for natural                  |
| **Live WPM Slider**| Change speed while typing                         | Drag anytime                        |
| **Strict WPM**     | Exact timing, no natural variations               | Keep OFF                            |
| **Jitter**         | Random speed variation (more = more human)        | 10–15%                              |
| **Enable Typos**   | Makes realistic typing mistakes                   | ON for realism                      |
| **Mistake %**      | How often typos happen                            | 2–5%                                |
| **Long Pauses**    | Occasional thinking pauses                        | ON for realism                      |
| **Newline Handling** | Controls what Enter does (keep Enter while typing code) | **Keep Enter ON for code** |
| **Code Mode**      | For typing code (ignores indentation)             | ON for code                         |


---

## 🔧 Troubleshooting

### "Python is not recognized"
- Reinstall Python and make sure to check **"Add Python to PATH"**
- Restart your computer after installing

### "pip is not recognized"  
- Try: `python -m pip install flask pynput`

### "Address already in use"
- Run `stop.vbs` first, then `start.vbs` again

### "Connection refused" or "Took too long to respond"
- Make sure you ran `start.vbs` (servers run in background)
- Check if ports 5000 and 8000 are allowed through firewall
- Try `http://127.0.0.1:8000` instead of `localhost:8000`

### Nothing happens when I click "Type on target"
- Click on the window where you want text to appear BEFORE clicking the button
- You have about 2 seconds to click the target window

### Remote access not working
- Both computers must be on the same WiFi/network
- Check firewall settings on target computer
- Make sure you're using the correct IP address

---

## 📁 Project Files

```
laptop-typist/
│
├── start.vbs              ← Double-click to start (silent, no window)
├── stop.vbs               ← Double-click to stop (silent, no window)
├── start.bat              ← Batch script (used by start.vbs)
├── stop.bat               ← Batch script (used by stop.vbs)
├── README.md              ← This file
│
├── helper/
│   └── typist_server.py   ← The typing brain
│
└── web-ui/
    ├── index.html         ← The control panel
    └── server.py          ← Serves the control panel
```

---

## 💡 Tips for Best Results

1. **Start slow** — Begin with 60-80 WPM and increase
2. **Use Code Mode** for programming code
3. **Keep typos ON** — Makes it look more realistic
4. **Adjust live** — Use the WPM slider while it's typing
5. **Test first** — Try on Notepad before important use

---

## ❓ FAQ

**Q: Is this safe?**  
A: Yes! It only simulates keyboard typing. It doesn't access any files or internet.

**Q: Can I use this for typing in any application?**  
A: Yes! Anywhere you can type — Word, Google Docs, code editors, chat apps, etc.

**Q: Does it work on Mac/Linux?**  
A: The typing engine works, but you'll need to run the Python files manually instead of using `.bat` files. It works on Mac/Linux, but **Windows is preferable** for easier setup and automation.  
I am currently **working on improving Mac/Linux support**.


**Q: Can I adjust speed while it's typing?**  
A: Yes! Use the "Live WPM" slider to change speed in real-time.

---
> ⚠️ **Do not use this tool for online assessments or any unauthorized purposes.**

## 🤝 Contributing

Found a bug or have an idea? [Open an issue](https://github.com/poshithNandyala/laptop-typist/issues)!

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

You are free to use, modify, and distribute this software.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/poshithNandyala">Poshith Nandyala</a>
</p>


