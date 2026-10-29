# Installation & Setup Guide

This guide covers setting up **AI Teammates for Counter-Strike: Condition Zero** on Windows.

## Prerequisites

1. **Counter-Strike: Condition Zero** installed on your PC.
2. **Python 3.10 or higher** installed and added to Windows PATH.
3. A working microphone (headset recommended to avoid audio echo).

---

## Step 1: Install Dependencies

Open PowerShell or Command Prompt in the repository root and run:
```powershell
py -m pip install edge-tts soundfile keyboard
```
*(Note: `openai-whisper`, `sounddevice`, `numpy`, and `requests` are already bundled or installable via standard pip).*

---

## Step 2: Configure Condition Zero

Run the automated game configurator:
```powershell
py main.py --setup
```
This updates:
- `czero/listenserver.cfg`: Enables real-time UDP logging on `127.0.0.1:27115` and enables RCON on `127.0.0.1:27015`.
- `czero/autoexec.cfg`: Ensures commands persist across map changes.
- `czero/BotProfile.db`: Adds custom bot profiles for **Vikram**, **Kabir**, **Marcus**, and **Sunny** with tailored weapons, skills, and skins.

*(Backups with `.backup` extension are automatically saved if you ever wish to restore defaults).*

---

## Step 3: Build the Voice Library (One-Time)

To guarantee zero latency and zero API cost during gameplay, generate the voice line library:
```powershell
py voice/builder.py
```
This downloads and caches high-fidelity emotional audio clips for all 4 teammates into `voice/library/`. You can also initiate this from the Command Center web dashboard.

---

## Step 4: Run the AI Teammates Service

Start the application:
```powershell
py main.py
```
The Command Center dashboard will open automatically in your browser at `http://localhost:5000`.

---

## Step 5: Start Condition Zero

1. Launch `Condition_Zero.exe`.
2. Click **New Game**, choose any map (e.g. `de_dust2`), and start.
3. Open the game console (`~`) and spawn your teammates:
```console
bot_add_ct Vikram
bot_add_ct Kabir
bot_add_ct Marcus
bot_add_ct Sunny
```
4. Hold the **`V`** key to speak to them via microphone, or type in team chat with `say_team`.
