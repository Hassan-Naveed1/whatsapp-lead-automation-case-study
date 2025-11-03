PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT DEFAULT 'wix_form',
    full_name TEXT,
    phone TEXT UNIQUE,
    email TEXT,
    status TEXT DEFAULT 'new',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (lead_id) REFERENCES leads (id)
);

CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    template TEXT NOT NULL,
    body TEXT NOT NULL,
    send_after TEXT NOT NULL,
    sent_at TEXT,
    attempts INTEGER DEFAULT 0,
    error TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads (id)
);

CREATE TABLE IF NOT EXISTS templates (
    name TEXT PRIMARY KEY,
    body TEXT NOT NULL,
    active INTEGER DEFAULT 1
);

-- ✅ 3 columns listed for 3 values (correct)
INSERT OR REPLACE INTO templates(name, body, active) VALUES
('welcome', 'Hi {first_name}! Thanks for reaching out to Drills Academy. I can help you book a free trial. Are mornings or evenings better?', 1),
('followup', 'Just checking in, {first_name} — would you like me to set up a trial this week?', 1);
