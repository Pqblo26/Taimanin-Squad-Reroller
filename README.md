# 🚀 Taimanin Squad Auto-Reroll Bot (ADB Edition)

A Python automation bot designed for mass, simultaneous rerolling in the game **Taimanin Squad** using Android emulators (optimized for MuMu Player 12). 

Instead of relying on screen clicks based on Windows coordinates, this bot works directly via **ADB (Android Debug Bridge)**. This means **you can minimize the emulators or use your PC normally** while the bot does the dirty work in the background.

## ✨ Key Features

* **⚡ True Multi-Instance:** Supports multiple emulators running at the same time via *multithreading*. Configured by default for 4 instances.
* **👁️ Database Recognition:** Uses `OpenCV` for image recognition (Template Matching). It scans for specific SSR character faces on the pull results screen.
* **🎯 100% Accurate:** By not relying on background colors or glow effects, it completely avoids common gacha false positives.
* **🛑 Auto-Stop & Alert:** When an instance detects your target number of SSR characters (default is 3), it stops immediately and plays a beep alert so you can manually confirm the pull.

## 🛠️ Prerequisites

1.  **Python 3.8+** installed on your system.
2.  The following Python libraries. You can install them by running:
    ```bash
    pip install opencv-python numpy Pillow
    ```
3.  **MuMu Player 12** (or any other emulator with ADB debugging enabled).

## 🚀 Installation and Setup

1.  **Clone this repository** or download the files.
2.  **Create the character database:**
    * Create a folder named `ssr_personajes` in the same directory as the script.
    * Add small `.png` crops of the SSR characters' faces (named `char1.png`, `char2.png`, etc.). 
    * *Crucial note:* The crops must be taken directly from a screenshot captured via ADB (`adb exec-out screencap -p > photo.png`) so the resolution scale matches the bot's vision perfectly.
3.  **Adjust the ADB path:**
    Open `taimanin_reroll_bot.py` and edit the `ADB_PATH` variable with your emulator's ADB path. Example for MuMu 12:
    ```python
    ADB_PATH = r"C:\Program Files\Netease\MuMuPlayer\nx_main\adb.exe"
    ```
4.  **Configure your instances:**
    Open a terminal, run `adb devices` to see your emulators' ports, and update the `INSTANCES` list in the code with your actual ports (e.g., `emulator-5560`).

## ⚠️ Important Notes

* **Internal Resolution:** The bot assumes the emulator's internal resolution output via ADB is **960x540**. 
* **Manual Confirmation:** The bot **NEVER** touches the "Confirm recruit" button. You are the one who decides when to keep the account.
* **To stop everything:** Press `Ctrl+C` in the terminal.

## 🎮 Usage

Once everything is set up and the game is open on the tutorial recruitment screen, simply run the bot:

```bash
python taimanin_reroll_botv2.py
