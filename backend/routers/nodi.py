from fastapi import APIRouter
import json
import os
import math
from collections import defaultdict
from db import get_conn
import hashlib

router = APIRouter()

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

def load_node_positions():
    with open(os.path.join(DATA, "node_positions.json"), "r") as f:
        return json.load(f)

def load_nomi():
    try:
        with open(os.path.join(DATA, "nodi_nomi.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def load_gw_positions():
    try:
        with open(os.path.join(DATA, "gateway_positions.json"), "r") as f:
            return json.load(f)
    except:
        return {}

@router.get("/")
def get_nodi(stato: str = None):
    conn = get_conn()
    cur = conn.cursor()

    if stato:
        cur.execute(
            "SELECT * FROM profilo_nodi WHERE stato = %s ORDER BY stato, rssi_medio",
            (stato.upper(),)
        )
    else:
        cur.execute("SELECT * FROM profilo_nodi ORDER BY stato, rssi_medio")

    rows = cur.fetchall()
    conn.close()

    pos  = load_node_positions()
    nomi = load_nomi()

    nodi = []
    for row in rows:
        deveui   = str(row["deveui"]).upper()
        node_pos = pos.get(deveui) or {}

        info_nome = nomi.get(deveui, {})
        nome = info_nome.get("nome", "")

        rssi = float(row["rssi_medio"]) if row["rssi_medio"] else -120.0
        sf   = float(row["sf_medio"])   if row["sf_medio"]   else 12.0
        gw   = int(row["n_gateway"])    if row["n_gateway"]  else 0

        iq = round(
            0.5 * max(0, min(1, (rssi + 140) / 90)) +
            0.5 * max(0, min(1, (12 - sf) / 5)),
            2
        )

        if gw == 1:
            if_base = 0.8
        elif gw == 2:
            if_base = 0.4
        else:
            if_base = 0.2
        indice_fragilita = round(if_base, 2)

        lat = node_pos.get("lat")
        lon = node_pos.get("lon")

        nodi.append({
            "deveui":           deveui,
            "stato":            str(row["stato"]),
            "rssi_medio":       round(rssi, 1),
            "sf_medio":         round(sf, 2),
            "snr_medio":        round(float(row["snr_medio"]), 1) if row["snr_medio"] else 0.0,
            "giorni_batteria":  None,
            "batteria_pct":     None,
            "indice_qualita":   iq,
            "indice_fragilita": indice_fragilita,
            "indice_tendenza":  None,
            "n_gateway":        gw,
            "lat":              lat,
            "lon":              lon,
            "nome":             nome,
            "marca":            "",
            "classificazione":  "",
            "trend":            "",
        })

    # Arricchisci con dati batteria
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (deveui)
               deveui, nome, marca, batteria_pct, ts_raccolta
        FROM snapshot_batteria
        ORDER BY deveui, ts_raccolta DESC
    """)
    batt_rows = cur.fetchall()
    conn.close()

    batt_map = {str(r["deveui"]).upper(): r for r in batt_rows}

    for nodo in nodi:
        b = batt_map.get(nodo["deveui"])
        if b:
            nodo["batteria_pct"] = float(b["batteria_pct"])
            if not nodo["nome"] and b["nome"]:
                nodo["nome"] = str(b["nome"])
            if not nodo["marca"] and b["marca"]:
                nodo["marca"] = str(b["marca"])

    # Aggiungi nodi in timeout
    deveui_con_profilo = {n["deveui"] for n in nodi}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT deveui, nome FROM nodi")
    tutti_nodi = cur.fetchall()
    conn.close()

    for n in tutti_nodi:
        deveui = str(n["deveui"]).upper()
        if deveui in deveui_con_profilo:
            continue

        nome = str(n["nome"]) if n["nome"] else ""
        if not nome:
            info_nome = nomi.get(deveui, {})
            nome = info_nome.get("nome", "")

        node_pos = pos.get(deveui) or {}
        lat = node_pos.get("lat")
        lon = node_pos.get("lon")

        nodi.append({
            "deveui":           deveui,
            "stato":            "TIMEOUT",
            "rssi_medio":       0.0,
            "sf_medio":         0.0,
            "snr_medio":        0.0,
            "giorni_batteria":  None,
            "batteria_pct":     None,
            "indice_qualita":   None,
            "indice_fragilita": None,
            "indice_tendenza":  None,
            "n_gateway":        0,
            "lat":              lat,
            "lon":              lon,
            "nome":             nome,
            "marca":            "",
            "classificazione":  "",
            "trend":            "",
        })

    # Grid layout per nodi con stesse coordinate
    coord_groups = defaultdict(list)
    for nodo in nodi:
        if nodo["lat"] and nodo["lon"]:
            key = (round(nodo["lat"], 4), round(nodo["lon"], 4))
            coord_groups[key].append(nodo)

    spacing = 0.0005
    for key, gruppo in coord_groups.items():
        if len(gruppo) <= 1:
            continue
        cols = math.ceil(math.sqrt(len(gruppo)))
        for i, nodo in enumerate(gruppo):
            row_i = i // cols
            col_i = i % cols
            nodo["lat"] = key[0] + row_i * spacing
            nodo["lon"] = key[1] + col_i * spacing

    return {"nodi": nodi}


@router.get("/{deveui}")
def get_nodo(deveui: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM profilo_nodi WHERE deveui = %s",
        (deveui.upper(),)
    )
    row = cur.fetchone()

    cur.execute("""
        SELECT gweui,
               COUNT(*) as n_pacchetti,
               AVG(rssi) as rssi_medio,
               AVG(snr) as snr_medio,
               AVG(sf) as sf_medio,
               MAX(ts_raccolta) as ultimo_contatto
        FROM snapshot_radio
        WHERE deveui = %s
        AND ts_raccolta > NOW() - INTERVAL '7 days'
        GROUP BY gweui
        ORDER BY n_pacchetti DESC
    """, (deveui.upper(),))
    gateway_nodo = cur.fetchall()

    cur.execute("""
        SELECT DATE(ts_raccolta) as data,
               AVG(rssi) as rssi_medio,
               AVG(sf) as sf_medio,
               COUNT(*) as n_pacchetti
        FROM snapshot_radio
        WHERE deveui = %s AND ts_raccolta > NOW() - INTERVAL '7 days'
        GROUP BY DATE(ts_raccolta)
        ORDER BY data
    """, (deveui.upper(),))
    storico = cur.fetchall()
    conn.close()

    if not row:
        return {"error": "nodo non trovato"}

    # Arricchisci gateway con nome
    gw_positions = load_gw_positions()
    gateway_list = []
    for g in gateway_nodo:
        gweui = str(g["gweui"]).upper()
        gw_info = gw_positions.get(gweui) or gw_positions.get(gweui.lower()) or {}
        nome_gw = gw_info.get("name", gweui[-8:])
        gateway_list.append({
            **dict(g),
            "nome": nome_gw
        })

    return {
        "profilo": dict(row),
        "storico": [dict(s) for s in storico],
        "gateway": gateway_list
    }