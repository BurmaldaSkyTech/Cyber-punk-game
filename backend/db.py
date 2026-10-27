# backend/db.py
import os, json
try:
    import psycopg
except Exception:
    psycopg = None

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