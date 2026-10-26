# 🚀 NovaAssistant

**NovaAssistant** is a lightweight, autonomous Telegram userbot daemon and developer assistant powered by **Telethon** and **Google Gemini Flash**.

It runs silently in the background of your operating system to handle live direct message interception, smart native Windows desktop notifications, and automated evening AI digests of tech and gaming channels.

---

## ✨ Features

- **🔔 Context-Aware Live DM Interception:**
  - Continuously monitors incoming direct messages.
  - Triggers native Windows Toast Notifications **only when your developer environment is active** (e.g., Antigravity IDE), keeping distractions to zero when you are away.
- **📰 Autonomous AI Evening Digest:**
  - Scheduled daily run (21:30–23:59).
  - Fetches updates from curated channel folders (`Dev & AI` and `Gaming`).
  - Synthesizes key takeaways, release notes, and news using **Gemini 3.5 Flash** (0 token cost on Google AI Studio Free Tier).
  - Posts the structured summary into a dedicated forum topic in your personal supergroup.
  - Automatically marks all scraped channels as read to keep your dialog list clean.
- **💬 Quick Reply CLI:**
  - Instant CLI tool (`send_reply.py`) to send Telegram replies directly from your terminal or AI coding agent turns.
- **🛡️ Rock-Solid Windows Daemon:**
  - Runs headless without open console windows via VBS launcher in `shell:startup`.

---

## 📁 Project Structure

```text
NovaAssistant/
├── nova_service.py       # Main background service (Listener + AI Digest + Scheduler)
├── send_reply.py         # CLI reply tool for quick messaging
├── .env.example          # Environment variables template
├── .gitignore            # Security filters (blocks session keys, logs, and secrets)
└── README.md             # Documentation
```

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- Dependencies:
  ```bash
  pip install telethon google-genai
  ```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

```env
TG_API_ID=your_telegram_api_id
TG_API_HASH=your_telegram_api_hash
TG_STORAGE_CHANNEL_ID=your_target_group_id
TG_DIGEST_TOPIC_ID=37
GEMINI_API_KEY=your_gemini_api_key
```

* Telegram API credentials: [my.telegram.org](https://my.telegram.org)
* Gemini API Key: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 3. First-Time Authorization
Run the service once in your terminal to complete Telegram SMS/app verification:
```bash
python nova_service.py
```
This generates your local session file (`userbot_session.session`).

### 4. Background Startup (Windows)
To run silently on Windows boot, add a launcher script to your Startup folder (`Win + R` -> `shell:startup`):
```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Dev\Bots\Telegram\NovaAssistant"
exe = chr(34) & "C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe" & chr(34)
arg = chr(34) & "D:\Dev\Bots\Telegram\NovaAssistant\nova_service.py" & chr(34)
WshShell.Run exe & " " & arg, 0, False
```

---

## 🔒 Security & Privacy

- All session data (`*.session`) and API keys (`.env`) are strictly ignored via `.gitignore` and never committed to version control.
- All requests communicate directly with official Telegram MTProto endpoints and Google Generative AI APIs over HTTPS.

---

## 📜 License
MIT License.
