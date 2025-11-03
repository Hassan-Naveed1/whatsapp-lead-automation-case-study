import sqlite3, json, datetime as dt
from typing import Dict, Any, List
from .settings import Settings

def _connect(db_path: str):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

class Repo:
    def __init__(self, s: Settings):
        self.s = s
        self.conn = _connect(s.DB_PATH)

class LeadRepo(Repo):
    def upsert_lead(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO leads(full_name, phone, email, source)
            VALUES(?,?,?,?)
            ON CONFLICT(phone) DO UPDATE SET
                full_name=excluded.full_name,
                email=excluded.email,
                updated_at=datetime('now')
        """, (data.get("full_name"), data.get("phone"), data.get("email"), data.get("source","wix_form")))
        self.conn.commit()
        cur = self.conn.execute("SELECT * FROM leads WHERE phone = ?", (data.get("phone"),))
        return dict(cur.fetchone())

    def add_event(self, lead_id: int, event_type: str, payload: Dict[str, Any]):
        self.conn.execute("""
            INSERT INTO events(lead_id, event_type, payload_json)
            VALUES(?,?,?)
        """, (lead_id, event_type, json.dumps(payload)))
        self.conn.commit()

class TemplateRepo(Repo):
    def get(self, name: str) -> str:
        cur = self.conn.execute("SELECT body FROM templates WHERE name=? AND active=1", (name,))
        row = cur.fetchone()
        return row[0] if row else ""

class OutboxRepo(Repo):
    def enqueue(self, lead_id: int, template: str, body: str, delay_min: int = 0):
        send_after = (dt.datetime.utcnow() + dt.timedelta(minutes=delay_min)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.conn.execute("""
            INSERT INTO outbox(lead_id, template, body, send_after) VALUES(?,?,?,?)
        """, (lead_id, template, body, send_after))
        self.conn.commit()

    def list_due(self, now_utc: dt.datetime, limit: int = 20) -> List[dict]:
        iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        cur = self.conn.execute("""
            SELECT * FROM outbox WHERE sent_at IS NULL AND send_after <= ?
            ORDER BY send_after ASC LIMIT ?
        """, (iso, limit))
        return [dict(r) for r in cur.fetchall()]

    def mark_sent(self, outbox_id: int):
        self.conn.execute("UPDATE outbox SET sent_at=datetime('now'), error=NULL WHERE id=?", (outbox_id,))
        self.conn.commit()

    def mark_error(self, outbox_id: int, err: str, attempts: int):
        self.conn.execute("UPDATE outbox SET attempts=?, error=? WHERE id=?", (attempts, err, outbox_id))
        self.conn.commit()

    def list_pending(self, limit: int = 50) -> List[dict]:
        cur = self.conn.execute("""
            SELECT * FROM outbox WHERE sent_at IS NULL ORDER BY send_after ASC LIMIT ?
        """, (limit,))
        return [dict(r) for r in cur.fetchall()]

class LeadService:
    def __init__(self, s: Settings):
        self.s = s
        self.leads = LeadRepo(s)
        self.tpl = TemplateRepo(s)
        self.outbox = OutboxRepo(s)

    def _first_name(self, full: str) -> str:
        return (full or "").split(" ")[0]

    def handle_form_intake(self, data: Dict[str, Any]) -> Dict[str, Any]:
        lead = self.leads.upsert_lead(data)
        self.leads.add_event(lead["id"], "wix_form", data)
        welcome = self.tpl.get("welcome").format(first_name=self._first_name(lead.get("full_name") or ""))
        self.outbox.enqueue(lead["id"], "welcome", welcome, delay_min=0)
        fu = self.tpl.get("followup").format(first_name=self._first_name(lead.get("full_name") or ""))
        self.outbox.enqueue(lead["id"], "followup", fu, delay_min=self.s.WA_FOLLOWUP_DELAY_MIN)
        return lead

    def handle_inbound_wa(self, form: Dict[str, Any]):
        phone = form.get("From", "").replace("whatsapp:", "")
        _ = form.get("Body", "").strip()
        lead = self.leads.upsert_lead({"full_name": "", "phone": phone, "email": None, "source": "inbound_wa"})
        self.leads.add_event(lead["id"], "inbound_wa", form)
        return lead
