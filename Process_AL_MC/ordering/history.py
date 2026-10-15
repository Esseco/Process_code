"""Atomic occupation claims and immutable completed observations shared by workers."""

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time

from .common import digest


class OccupationStore:
    def __init__(self, path, identity):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.binding = digest(identity)
        with self.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS records (key TEXT PRIMARY KEY, tm_key TEXT NOT NULL, occupation TEXT NOT NULL, status TEXT NOT NULL, owner TEXT, result TEXT, error TEXT, updated REAL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS counters (owner TEXT PRIMARY KEY, calls INTEGER NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS reconciliations (key TEXT, note TEXT, time REAL)"
            )
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('binding',?)", (self.binding,))
            if (
                db.execute("SELECT value FROM metadata WHERE name='binding'").fetchone()[0]
                != self.binding
            ):
                raise ValueError("History belongs to a different H/reference/model/settings")

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def claim(self, key, tm_key, occupation, owner, *, budget=None):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM records WHERE key=?", (key,)).fetchone()
            if row and row["status"] == "completed":
                return {"status": "cached", "result": json.loads(row["result"])}
            if row and row["status"] in {"running", "failed"}:
                return {"status": "busy" if row["status"] == "running" else "failed"}
            db.execute("INSERT OR IGNORE INTO counters VALUES (?,0)", (owner,))
            count = db.execute("SELECT calls FROM counters WHERE owner=?", (owner,)).fetchone()[0]
            if budget is not None and count >= budget:
                return {"status": "budget_limit"}
            db.execute(
                "INSERT INTO records VALUES (?,?,?,'running',?,NULL,NULL,?) ON CONFLICT(key) DO UPDATE SET status='running',owner=excluded.owner,updated=excluded.updated",
                (key, tm_key, json.dumps(occupation, sort_keys=True), owner, time.time()),
            )
            db.execute("UPDATE counters SET calls=calls+1 WHERE owner=?", (owner,))
            return {"status": "claimed"}

    def complete(self, key, owner, result):
        with self.transaction() as db:
            changed = db.execute(
                "UPDATE records SET status='completed',result=?,updated=? WHERE key=? AND owner=? AND status='running'",
                (json.dumps(result, allow_nan=False), time.time(), key, owner),
            ).rowcount
            if changed != 1:
                raise RuntimeError("Worker does not own this running occupation")

    def fail(self, key, owner, error):
        with self.transaction() as db:
            db.execute(
                "UPDATE records SET status='failed',error=?,updated=? WHERE key=? AND owner=? AND status='running'",
                (str(error)[:2000], time.time(), key, owner),
            )

    def records(self):
        with self.transaction() as db:
            rows = [dict(row) for row in db.execute("SELECT * FROM records ORDER BY key")]
        for row in rows:
            row["occupation"] = json.loads(row["occupation"])
            row["result"] = json.loads(row["result"]) if row["result"] else None
        return rows

    def count_completed(self):
        with self.transaction() as db:
            return db.execute("SELECT count(*) FROM records WHERE status='completed'").fetchone()[0]

    def calls(self, owner):
        with self.transaction() as db:
            row = db.execute("SELECT calls FROM counters WHERE owner=?", (owner,)).fetchone()
            return row[0] if row else 0

    def reconcile(self, key, *, verified_not_running, note):
        if verified_not_running is not True or not str(note).strip():
            raise ValueError("Explicit verified_not_running and evidence note are required")
        with self.transaction() as db:
            row = db.execute("SELECT status FROM records WHERE key=?", (key,)).fetchone()
            if not row or row[0] not in {"running", "failed"}:
                raise ValueError("Only interrupted/failed work can be reconciled")
            db.execute(
                "UPDATE records SET status='pending',owner=NULL,updated=? WHERE key=?",
                (time.time(), key),
            )
            db.execute("INSERT INTO reconciliations VALUES (?,?,?)", (key, str(note), time.time()))
