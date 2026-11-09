# backend/db.py
import os, json
try:
    import psycopg
except Exception:
    psycopg = None
import json as _json

DSN = os.environ.get("PG_DSN", "postgresql://postgres:412321@localhost:7777/cpr")
_conn = None


def conn():
    global _conn
    if psycopg is None:
        return None
    if _conn is None or _conn.closed:
        try:
            _conn = psycopg.connect(DSN, connect_timeout=5)
        except Exception:
            _conn = None
    return _conn


def family_rows(family):
    c = conn()
    if not c:
        return []
    try:
        with c.cursor() as cur:
            cur.execute("SELECT data FROM game_data WHERE family=%s", (family,))
            return [r[0] for r in cur.fetchall()]
    except Exception:
        return []


def family_map(family, fallback=None):
    import re as _re
    rows = family_rows(family)
    if not rows:
        return fallback or {}
    out = {}
    for r in rows:
        name = (r.get("name") or r.get("level") or r.get("condition")
                or r.get("category") or r.get("item") or "")
        key = _re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or "unknown"
        out[key] = r
    return out


def log_turn(sid, turn_no, player, action_text, judge, mechanics, narration):
    c = conn()
    if not c:
        return None
    try:
        with c.cursor() as cur:
            cur.execute("""INSERT INTO turns
                (session_id, turn_no, player, action_text, judge, mechanics, narration)
                VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (sid, turn_no, player, action_text,
                 json.dumps(judge, ensure_ascii=False),
                 json.dumps(mechanics, ensure_ascii=False), narration))
            tid = cur.fetchone()[0]
        c.commit()
        return tid
    except Exception:
        return None


def rate_turn(tid, rating, edited=None):
    c = conn()
    if not c:
        return
    with c.cursor() as cur:
        cur.execute("UPDATE turns SET rating=%s, edited_narration=COALESCE(%s, edited_narration) WHERE id=%s",
                    (rating, edited, tid))
    c.commit()

def _init_sessions_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            sid TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def save_session(sid, state):
    conn = _get_conn()  # замени на свой способ получения соединения
    _init_sessions_table(conn)
    conn.execute(
        "INSERT OR REPLACE INTO sessions (sid, state, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (sid, _json.dumps(state, ensure_ascii=False, default=str))
    )
    conn.commit()


def load_session(sid):
    conn = _get_conn()
    _init_sessions_table(conn)
    row = conn.execute("SELECT state FROM sessions WHERE sid = ?", (sid,)).fetchone()
    return _json.loads(row[0]) if row else None


def all_session_states():
    conn = _get_conn()
    _init_sessions_table(conn)
    rows = conn.execute("SELECT state FROM sessions").fetchall()
    return [_json.loads(r[0]) for r in rows]    
    
# === ПЕРСИСТЕНТНЫЕ СЕССИИ ===

def _ensure_sessions_table():
    c = conn()
    if not c:
        return False
    try:
        with c.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    sid TEXT PRIMARY KEY,
                    state JSONB NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
        c.commit()
        return True
    except Exception:
        try:
            c.rollback()
        except Exception:
            pass
        return False


def save_session(sid, state):
    if not _ensure_sessions_table():
        return False
    c = conn()
    if not c:
        return False
    try:
        with c.cursor() as cur:
            cur.execute(
                """INSERT INTO sessions (sid, state, updated_at)
                   VALUES (%s, %s, CURRENT_TIMESTAMP)
                   ON CONFLICT (sid) DO UPDATE
                   SET state = EXCLUDED.state, updated_at = CURRENT_TIMESTAMP""",
                (sid, _json.dumps(state, ensure_ascii=False, default=str))
            )
        c.commit()
        return True
    except Exception:
        try:
            c.rollback()
        except Exception:
            pass
        return False


def load_session(sid):
    if not _ensure_sessions_table():
        return None
    c = conn()
    if not c:
        return None
    try:
        with c.cursor() as cur:
            cur.execute("SELECT state FROM sessions WHERE sid = %s", (sid,))
            row = cur.fetchone()
        if not row:
            return None
        # psycopg возвращает jsonb уже как dict/list, строку парсим на всякий случай
        if isinstance(row[0], str):
            return _json.loads(row[0])
        return row[0]
    except Exception:
        return None


def all_session_states():
    if not _ensure_sessions_table():
        return []
    c = conn()
    if not c:
        return []
    try:
        with c.cursor() as cur:
            cur.execute("SELECT state FROM sessions")
            rows = cur.fetchall()
        out = []
        for (r,) in rows:
            if isinstance(r, str):
                try:
                    out.append(_json.loads(r))
                except Exception:
                    continue
            else:
                out.append(r)
        return out
    except Exception:
        return []    