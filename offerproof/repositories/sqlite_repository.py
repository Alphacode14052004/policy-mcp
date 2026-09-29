import json
import sqlite3
from contextlib import contextmanager


class SQLiteRepository:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS journeys (
                    id TEXT PRIMARY KEY, version INTEGER NOT NULL, state TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS idempotency (
                    merchant TEXT NOT NULL, agent TEXT NOT NULL, key TEXT NOT NULL,
                    payload_digest TEXT NOT NULL, response TEXT NOT NULL,
                    PRIMARY KEY (merchant, agent, key));
                CREATE TABLE IF NOT EXISTS disclosure_snapshots (
                    snapshot_id TEXT PRIMARY KEY, journey_id TEXT NOT NULL, disclosure_digest TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS snapshot_no_update BEFORE UPDATE ON disclosure_snapshots BEGIN
                    SELECT RAISE(ABORT, 'Append-only snapshot'); END;
                CREATE TRIGGER IF NOT EXISTS snapshot_no_delete BEFORE DELETE ON disclosure_snapshots BEGIN
                    SELECT RAISE(ABORT, 'Append-only snapshot'); END;
                CREATE TABLE IF NOT EXISTS audit (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
                    invocation_id TEXT NOT NULL, journey_id TEXT, event_type TEXT NOT NULL,
                    outcome TEXT NOT NULL, occurred_at TEXT NOT NULL, payload TEXT NOT NULL,
                    previous_event_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN
                    SELECT RAISE(ABORT, 'Append-only audit'); END;
                CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN
                    SELECT RAISE(ABORT, 'Append-only audit'); END;
            """)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA synchronous=FULL")
        try:
            yield connection
        finally:
            connection.close()

    def load(self, connection, ident):
        row = connection.execute("SELECT body FROM journeys WHERE id=?", (ident,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, connection, journey):
        from offerproof.security.digests import canonical
        connection.execute("INSERT INTO journeys(id,version,state,body) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET version=excluded.version,state=excluded.state,body=excluded.body",
            (journey["id"], journey["version"], journey["state"], canonical(journey)))
