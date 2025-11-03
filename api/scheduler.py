import time, datetime as dt, sqlite3
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from .services import OutboxRepo
from .settings import Settings

def run_scheduler_forever():
    S = Settings.from_env()
    outbox = OutboxRepo(S)
    print("[scheduler] started (TWILIO_TEST_MODE=%s)" % S.TWILIO_TEST_MODE)
    tw = None
    if not S.TWILIO_TEST_MODE:
        tw = Client(S.TWILIO_ACCOUNT_SID, S.TWILIO_AUTH_TOKEN)

    while True:
        due = outbox.list_due(dt.datetime.utcnow(), limit=10)
        for item in due:
            try:
                conn = sqlite3.connect(S.DB_PATH)
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT phone FROM leads WHERE id=?", (item["lead_id"],)).fetchone()
                phone = row["phone"] if row else None
                if not phone:
                    outbox.mark_error(item["id"], "no phone", attempts=item["attempts"]+1)
                    continue

                if S.TWILIO_TEST_MODE:
                    print(f"[scheduler] TEST -> {phone}: {item['body']}")
                else:
                    tw.messages.create(
                        from_=S.TWILIO_WHATSAPP_FROM,
                        to=f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone,
                        body=item["body"]
                    )
                outbox.mark_sent(item["id"])
                print(f"[scheduler] sent outbox#{item['id']} -> {phone}")
            except TwilioRestException as e:
                outbox.mark_error(item["id"], f"twilio:{e.code}", attempts=item["attempts"]+1)
            except Exception as e:
                outbox.mark_error(item["id"], str(e), attempts=item["attempts"]+1)
        time.sleep(3)
