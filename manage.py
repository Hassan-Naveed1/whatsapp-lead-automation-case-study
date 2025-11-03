#!/usr/bin/env python
# manage.py — single entrypoint for db init, checks, running API, and scheduler.

import argparse, os, sys, sqlite3, textwrap
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))  # ensure local imports

from api.settings import Settings

DB_PATH = ROOT / "db" / "app.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"

def ok(m): print("✅", m)
def warn(m): print("⚠️ ", m)
def err(m): print("❌", m)

def cmd_db(args):
    """Create/upgrade DB schema (idempotent)."""
    DB_PATH.parent.mkdir(exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    if args.reset and DB_PATH.exists():
        DB_PATH.unlink()
        warn(f"Removed existing DB at {DB_PATH}")

    con = sqlite3.connect(DB_PATH.as_posix())
    try:
        con.executescript(schema)
        con.commit()
        ok(f"Database ready at {DB_PATH}")
    except sqlite3.OperationalError as e:
        err(f"DB init error: {e}")
        sys.exit(2)
    finally:
        con.close()

def cmd_check(_args):
    """Preflight diagnostics: env, DB, tables, templates, test mode."""
    S = Settings.from_env()
    missing = []
    for k in ["DB_PATH","TWILIO_ACCOUNT_SID","TWILIO_AUTH_TOKEN","TWILIO_WHATSAPP_FROM"]:
        if not getattr(S, k, None):
            missing.append(k)
    if missing:
        warn("Missing env vars: " + ", ".join(missing))
        print("→ Copy .env.example to .env and fill the values.")
    else:
        ok("Environment loaded")

    if not Path(S.DB_PATH).exists():
        warn(f"DB not found at {S.DB_PATH} → run: python manage.py db")
        return
    else:
        ok(f"DB found at {S.DB_PATH}")

    con = sqlite3.connect(S.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        need = {"leads","events","outbox","templates"}
        missing = need - tables
        if missing:
            warn(f"Missing tables: {sorted(list(missing))} → run: python manage.py db --reset")
        else:
            ok("All required tables exist")
        tmpl = [r["name"] for r in con.execute("SELECT name FROM templates WHERE active=1")]
        if not tmpl:
            warn("No active templates. Re-run: python manage.py db")
        else:
            ok("Active templates: " + ", ".join(tmpl))
    finally:
        con.close()

    if S.TWILIO_TEST_MODE:
        warn("TWILIO_TEST_MODE=true → messages will NOT be sent (safe for dev)")
    else:
        ok("TWILIO_TEST_MODE=false → live sends enabled")

def cmd_run(_args):
    os.environ.setdefault("FLASK_APP", "api.app:app")
    os.execvp(sys.executable, [sys.executable, "-m", "flask", "run", "-p", "5000"])

def cmd_scheduler(_args):
    from api.scheduler import run_scheduler_forever
    run_scheduler_forever()

def main():
    p = argparse.ArgumentParser(
        description="WhatsApp Lead Automation manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Common:
              python manage.py check
              python manage.py db            # create/upgrade DB + seed
              python manage.py db --reset    # recreate DB from scratch
              python manage.py run
              python manage.py scheduler
        """)
    )
    sub = p.add_subparsers(dest="cmd")

    p_db = sub.add_parser("db", help="Initialize or reset database")
    p_db.add_argument("--reset", action="store_true", help="Delete DB then recreate")
    p_db.set_defaults(func=cmd_db)

    p_check = sub.add_parser("check", help="Preflight diagnostics")
    p_check.set_defaults(func=cmd_check)

    p_run = sub.add_parser("run", help="Run Flask API")
    p_run.set_defaults(func=cmd_run)

    p_sched = sub.add_parser("scheduler", help="Run scheduler loop")
    p_sched.set_defaults(func=cmd_scheduler)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()
