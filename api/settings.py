import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    DB_PATH: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str
    TWILIO_TEST_MODE: bool
    WA_FOLLOWUP_DELAY_MIN: int

    @classmethod
    def from_env(cls):
        return cls(
            DB_PATH=os.getenv("DB_PATH", "db/app.db"),
            TWILIO_ACCOUNT_SID=os.getenv("TWILIO_ACCOUNT_SID", ""),
            TWILIO_AUTH_TOKEN=os.getenv("TWILIO_AUTH_TOKEN", ""),
            TWILIO_WHATSAPP_FROM=os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"),
            TWILIO_TEST_MODE=os.getenv("TWILIO_TEST_MODE", "true").lower() == "true",
            WA_FOLLOWUP_DELAY_MIN=int(os.getenv("WA_FOLLOWUP_DELAY_MIN", "30")),
        )
