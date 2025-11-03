# WhatsApp Lead Automation System

Automated WhatsApp follow-ups for new leads using **Flask + Twilio API + SQLite**.  
When someone fills out a form (or sends a WhatsApp message), the system:
1. Welcomes them automatically.
2. Sends a follow-up message after a delay (configurable).
3. Logs every event into a simple SQLite database.

---

## 🎯 Features

- Flask API endpoints for form submissions (`/api/wix-form`) and WhatsApp webhooks (`/api/wa-webhook`)
- Scheduler that dispatches queued messages automatically (APScheduler style loop)
- SQLite database with three main tables: `leads`, `events`, and `outbox`
- Fully local and Twilio Sandbox-ready (no cloud DB required)
- Environment variables via `.env`
- Test mode toggle to simulate messages without sending

---

## 🗂️ Repository Structure


---

## ⚙️ Local Setup

### 1️⃣ Clone & install
```bash
git clone https://github.com/<your-username>/whatsapp-lead-automation-case-study.git
cd whatsapp-lead-automation-case-study
python -m venv .venv
# Git Bash on Windows:
source .venv/Scripts/activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt