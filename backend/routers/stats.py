from fastapi import APIRouter
from db import get_conn

router = APIRouter()

@router.get("/")
def get_stats():
    conn = get_conn()
    cur = conn.cursor()

    # Nodi con profilo radio (attivi)
    cur.execute("""
        SELECT
            COUNT(*) as attivi,
            SUM(CASE WHEN stato = 'CRITICO'    THEN 1 ELSE 0 END) as critici,
            SUM(CASE WHEN stato = 'ATTENZIONE' THEN 1 ELSE 0 END) as attenzione,
            SUM(CASE WHEN stato = 'OK'         THEN 1 ELSE 0 END) as ok
        FROM profilo_nodi
    """)
    profilo = dict(cur.fetchone())

    # Totale nodi in anagrafica
    cur.execute("SELECT COUNT(*) as totale FROM profilo_nodi")
    totale = dict(cur.fetchone())

    # Gateway attivi
    cur.execute("""
        SELECT COUNT(DISTINCT gweui) as totale
        FROM snapshot_radio
        WHERE ts_raccolta > NOW() - INTERVAL '7 days'
    """)
    gw = dict(cur.fetchone())

    # Batterie critiche
    cur.execute("""
        SELECT COUNT(*) as critici
        FROM (
            SELECT DISTINCT ON (deveui) deveui, batteria_pct
            FROM snapshot_batteria
            ORDER BY deveui, ts_raccolta DESC
        ) sub
        WHERE batteria_pct < 20
    """)
    batt = dict(cur.fetchone())

    conn.close()
    return {
        "nodi": {
            "totale":     totale["totale"],
            "attivi":     profilo["attivi"],
            "critici":    profilo["critici"],
            "attenzione": profilo["attenzione"],
            "ok":         profilo["ok"],
        },
        "gateway": {"totale": gw["totale"]},
        "batteria_critici": batt["critici"],
    }