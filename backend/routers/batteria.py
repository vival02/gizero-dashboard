from fastapi import APIRouter
from db import get_conn

router = APIRouter()

@router.get("/")
def get_batteria():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (deveui)
               deveui, nome, marca, batteria_pct, volt, ts_raccolta
        FROM snapshot_batteria
        ORDER BY deveui, ts_raccolta DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return {"batteria": [dict(r) for r in rows]}

@router.get("/critici")
def get_critici():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (deveui)
               deveui, nome, marca, batteria_pct, ts_raccolta
        FROM snapshot_batteria
        WHERE batteria_pct < 20
        ORDER BY deveui, ts_raccolta DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return {"critici": [dict(r) for r in rows]}