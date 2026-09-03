"""
Database layer using SQLite via Python's built-in sqlite3.
All tables are created on first run; no external DB server required.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("donation_platform.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ── Donors ────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            age         INTEGER NOT NULL,
            gender      TEXT    NOT NULL,
            blood_type  TEXT    NOT NULL,
            phone       TEXT    NOT NULL,
            email       TEXT,
            city        TEXT    NOT NULL,
            state       TEXT    NOT NULL,
            country     TEXT    NOT NULL DEFAULT 'India',
            lat         REAL,
            lon         REAL,
            organs      TEXT    NOT NULL DEFAULT '[]',   -- JSON list
            available   INTEGER NOT NULL DEFAULT 1,
            registered_at TEXT  NOT NULL
        )
    """)

    # ── Urgent Requests ───────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name    TEXT    NOT NULL,
            age             INTEGER NOT NULL,
            gender          TEXT    NOT NULL,
            blood_type      TEXT    NOT NULL,
            phone           TEXT    NOT NULL,
            email           TEXT,
            hospital        TEXT    NOT NULL,
            city            TEXT    NOT NULL,
            state           TEXT    NOT NULL,
            country         TEXT    NOT NULL DEFAULT 'India',
            lat             REAL,
            lon             REAL,
            needed_organ    TEXT    NOT NULL,
            urgency         TEXT    NOT NULL DEFAULT 'High',
            notes           TEXT,
            status          TEXT    NOT NULL DEFAULT 'Open',
            posted_at       TEXT    NOT NULL
        )
    """)

    # ── Matches ────────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id  INTEGER NOT NULL REFERENCES requests(id),
            donor_id    INTEGER NOT NULL REFERENCES donors(id),
            score       REAL    NOT NULL,
            ai_notes    TEXT,
            status      TEXT    NOT NULL DEFAULT 'Pending',
            matched_at  TEXT    NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ── Donor CRUD ─────────────────────────────────────────────────────────────────

def add_donor(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO donors
            (name, age, gender, blood_type, phone, email,
             city, state, country, lat, lon, organs, available, registered_at)
        VALUES
            (:name,:age,:gender,:blood_type,:phone,:email,
             :city,:state,:country,:lat,:lon,:organs,:available,:registered_at)
    """, {
        **data,
        "organs": json.dumps(data.get("organs", [])),
        "available": 1,
        "registered_at": datetime.now().isoformat(timespec="seconds"),
    })
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_donors() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM donors WHERE available=1 ORDER BY registered_at DESC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["organs"] = json.loads(d["organs"])
        result.append(d)
    return result


def get_donor_by_id(donor_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM donors WHERE id=?", (donor_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["organs"] = json.loads(d["organs"])
        return d
    return None


def update_donor_availability(donor_id: int, available: bool):
    conn = get_connection()
    conn.execute("UPDATE donors SET available=? WHERE id=?", (int(available), donor_id))
    conn.commit()
    conn.close()


# ── Request CRUD ───────────────────────────────────────────────────────────────

def add_request(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO requests
            (patient_name, age, gender, blood_type, phone, email,
             hospital, city, state, country, lat, lon,
             needed_organ, urgency, notes, status, posted_at)
        VALUES
            (:patient_name,:age,:gender,:blood_type,:phone,:email,
             :hospital,:city,:state,:country,:lat,:lon,
             :needed_organ,:urgency,:notes,:status,:posted_at)
    """, {
        **data,
        "status": "Open",
        "posted_at": datetime.now().isoformat(timespec="seconds"),
    })
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_requests(status: str | None = None) -> list[dict]:
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM requests WHERE status=? ORDER BY posted_at DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM requests ORDER BY posted_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_request_by_id(req_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM requests WHERE id=?", (req_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_request_status(req_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE requests SET status=? WHERE id=?", (status, req_id))
    conn.commit()
    conn.close()


# ── Match CRUD ─────────────────────────────────────────────────────────────────

def save_matches(matches: list[dict]):
    conn = get_connection()
    conn.execute("DELETE FROM matches WHERE request_id=?", (matches[0]["request_id"],))
    conn.executemany("""
        INSERT INTO matches (request_id, donor_id, score, ai_notes, status, matched_at)
        VALUES (:request_id,:donor_id,:score,:ai_notes,:status,:matched_at)
    """, [
        {**m, "matched_at": datetime.now().isoformat(timespec="seconds")}
        for m in matches
    ])
    conn.commit()
    conn.close()


def get_matches_for_request(req_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.*, d.name AS donor_name, d.phone AS donor_phone,
               d.city AS donor_city, d.state AS donor_state, d.blood_type AS donor_bt
        FROM matches m
        JOIN donors d ON d.id = m.donor_id
        WHERE m.request_id=?
        ORDER BY m.score DESC
    """, (req_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
