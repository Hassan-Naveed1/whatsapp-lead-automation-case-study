from flask import Flask, request, jsonify
from dotenv import load_dotenv
from .services import LeadService, OutboxRepo
from .settings import Settings

load_dotenv()
app = Flask(__name__)
S = Settings.from_env()
service = LeadService(S)

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/api/wix-form")
def wix_form():
    data = request.get_json(force=True, silent=True) or {}
    lead = service.handle_form_intake(data)
    return jsonify({"status": "ok", "lead_id": lead["id"]})

@app.post("/api/wa-webhook")
def wa_webhook():
    # In production, verify Twilio signature.
    form = request.form.to_dict()
    service.handle_inbound_wa(form)
    return ("", 204)

@app.get("/outbox")
def outbox():
    ob = OutboxRepo(S).list_pending(limit=50)
    return jsonify(ob)
