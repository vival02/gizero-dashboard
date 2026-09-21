"""
COLLECTOR AUTOMATICO — LoRaWAN GiZero
Versione PostgreSQL — adattato da collector_automatico.py
Logica identica, solo il database cambia da SQLite a PostgreSQL.
"""
import requests
import json
import os
import time
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import traceback
# ══════════════════════════════════════════════
# CONFIGURAZIONE
# ══════════════════════════════════════════════
BASE_URL  = "https://gizero.resiot.io/api"
TOKEN     = os.environ.get("RESIOT_TOKEN", "0d126be8225daa1a384f980cfc79f952")
HEADERS   = {"Accept": "application/json", "Grpc-Metadata-Authorization": TOKEN}

DB_HOST   = os.environ.get("POSTGRES_HOST", "localhost")
DB_NAME   = os.environ.get("POSTGRES_DB",   "gizero")
DB_USER   = os.environ.get("POSTGRES_USER", "gizero")
DB_PASS   = os.environ.get("POSTGRES_PASSWORD", "cambia_questa_password")

INTERVALLO_ORE   = 12
GIORNI_OVERLAP   = 6
PAUSA_TRA_NODI   = 0.15
MAX_PKT_PER_NODO = 200

# ══════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════
def get_conn():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


# ══════════════════════════════════════════════
# DECODER BATTERIA (identici all'originale)
# ══════════════════════════════════════════════
def dec_milesight(h):
    try: b = bytes.fromhex(h)
    except: return None, None
    i, n = 0, len(b)
    while i < n - 1:
        c, t = b[i], b[i+1]; i += 2
        if c == 0x01 and t == 0x75:
            return (float(b[i]), None) if i < n else (None, None)
        elif c in (0x03,0x04) and t == 0xc8: i += 4
        elif c in (0x03,0x04) and t in (0x00,0x01): i += 1
        elif c in (0x05,0x06) and t == 0xe2: i += 8
        elif c == 0x03 and t == 0x67: i += 2
        elif c == 0x04 and t == 0x68: i += 1
        elif c == 0xff and t == 0x0e:
            if i+1 < n:
                l = {0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:4}[b[i+1] & 0x07]
                i += 2 + l
            else: break
        else: break
    return None, None

def _volt_to_pct(v, vmax=3.6):
    return round(min(v/vmax*100, 100.0), 1)

def dec_dragino(h):
    try: b = bytes.fromhex(h)
    except: return None, None
    if len(b) < 2: return None, None
    v = ((b[0] << 8 | b[1]) & 0x3FFF) / 1000.0
    return (_volt_to_pct(v), round(v,3)) if 1.5 <= v <= 4.5 else (None, None)

def dec_watteco(h):
    try: b = bytes.fromhex(h)
    except: return None, None
    idx = b.find(b'\x00\x50\x00\x06')
    if idx != -1 and len(b) >= idx+10 and b[idx+4] == 0x41:
        l = b[idx+5]
        if l >= 5:
            mv = (b[idx+8] << 8) | b[idx+9]
            v  = mv / 1000.0
            return (_volt_to_pct(v), round(v,3)) if 2.0 <= v <= 4.2 else (None, None)
    return None, None

def dec_netvox(h):
    try: b = bytes.fromhex(h)
    except: return None, None
    if len(b) >= 4 and b[0] == 0x01:
        v = b[3] / 10.0
        return (_volt_to_pct(v), round(v,3)) if 2.0 <= v <= 4.0 else (None, None)
    return None, None

def dec_elsys(h):
    try: b = bytes.fromhex(h)
    except: return None, None
    lunghezze = {0x01:3,0x02:2,0x03:3,0x04:3,0x05:2,0x06:3,0x08:3,0x09:3,
                 0x0a:3,0x0b:3,0x0c:3,0x0d:5,0x0e:3,0x0f:2,0x10:4,0x11:3,0x12:5}
    i = 0
    while i < len(b) - 2:
        t = b[i]
        if t == 0x07:
            mv = (b[i+1] << 8) | b[i+2]
            v  = mv / 1000.0
            return (_volt_to_pct(v), round(v,3)) if 2.0 <= v <= 4.0 else (None, None)
        i += lunghezze.get(t, 1)
    return None, None

DECODERS = {
    "Milesight": dec_milesight, "Dragino": dec_dragino,
    "Watteco": dec_watteco, "Netvox": dec_netvox, "Elsys": dec_elsys,
}

MARCHE_KEYWORDS = {
    "Milesight": ["milesight"], "Dragino": ["dragino"],
    "Watteco": ["watteco"], "Netvox": ["netvox"], "Elsys": ["elsys"],
}

def identifica_marca(nome):
    n = nome.lower()
    for marca, keywords in MARCHE_KEYWORDS.items():
        if any(k in n for k in keywords):
            return marca
    return None

def popola_nodi(conn, session):
    """Popola la tabella nodi se vuota."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM nodi")
        if cur.fetchone()[0] > 0:
            return
    try:
        r = session.get(f"{BASE_URL}/application/nodes",
                       headers=HEADERS,
                       params={"limit": 1000, "offset": 0},
                       timeout=60)
        if r.status_code == 200:
            nodi = r.json().get("result", [])
            records = [(n.get("devEUI","").upper().strip(),
                       n.get("name","").strip(), True)
                      for n in nodi if n.get("devEUI")]
            with conn.cursor() as cur:
                execute_values(cur, """
                    INSERT INTO nodi (deveui, nome, attivo)
                    VALUES %s
                    ON CONFLICT (deveui) DO UPDATE SET nome = EXCLUDED.nome
                """, records)
            conn.commit()
            log.info(f"Tabella nodi popolata: {len(records)} nodi")
    except Exception as e:
        log.warning(f"Errore popolamento nodi: {e}")
        conn.rollback()

# ══════════════════════════════════════════════
# SESSION HTTP
# ══════════════════════════════════════════════
def get_session():
    s = requests.Session()
    retry = requests.adapters.Retry(
        total=3, backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"])
    s.mount("https://", requests.adapters.HTTPAdapter(max_retries=retry))
    return s


# ══════════════════════════════════════════════
# VERIFICA CONNESSIONE
# ══════════════════════════════════════════════
def verifica_connessione(session, max_tentativi=10, pausa_minuti=5):
    for tentativo in range(1, max_tentativi + 1):
        try:
            r = session.get(f"{BASE_URL}/application/nodes/status",
                           headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        log.warning(f"Connessione non disponibile (tentativo {tentativo}/{max_tentativi}), "
                   f"riprovo tra {pausa_minuti} minuti...")
        time.sleep(pausa_minuti * 60)
    log.error("Connessione assente dopo tutti i tentativi, ciclo saltato.")
    return False


# ══════════════════════════════════════════════
# AGGIORNA PROFILO CONSOLIDATO
# ══════════════════════════════════════════════
def aggiorna_profilo(conn):
    """Ricalcola profilo_nodi dagli ultimi 7 giorni di snapshot_radio."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO profilo_nodi (
                deveui, ts_aggiornamento, stato,
                rssi_medio, sf_medio, snr_medio, n_gateway
            )
            SELECT
                deveui,
                NOW(),
                CASE
                    WHEN AVG(rssi) <= -110 OR AVG(sf) >= 11 THEN 'CRITICO'
                    WHEN AVG(rssi) <= -100 OR AVG(sf) >= 10 THEN 'ATTENZIONE'
                    ELSE 'OK'
                END,
                ROUND(AVG(rssi)::numeric, 1),
                ROUND(AVG(sf)::numeric, 2),
                ROUND(AVG(snr)::numeric, 1),
                COUNT(DISTINCT gweui)
            FROM snapshot_radio
            WHERE ts_raccolta > NOW() - INTERVAL '7 days'
            GROUP BY deveui
            ON CONFLICT (deveui) DO UPDATE SET
                ts_aggiornamento = EXCLUDED.ts_aggiornamento,
                stato            = EXCLUDED.stato,
                rssi_medio       = EXCLUDED.rssi_medio,
                sf_medio         = EXCLUDED.sf_medio,
                snr_medio        = EXCLUDED.snr_medio,
                n_gateway        = EXCLUDED.n_gateway
        """)
    conn.commit()
    log.info("Profilo consolidato aggiornato")


# ══════════════════════════════════════════════
# RETENTION
# ══════════════════════════════════════════════
def applica_retention(conn):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM snapshot_radio WHERE ts_raccolta < NOW() - INTERVAL '14 days'"
        )
        deleted_radio = cur.rowcount
        cur.execute(
            "DELETE FROM snapshot_batteria WHERE ts_raccolta < NOW() - INTERVAL '30 days'"
        )
        deleted_batt = cur.rowcount
    conn.commit()
    log.info(f"Retention: rimossi {deleted_radio} radio, {deleted_batt} batteria")


# ══════════════════════════════════════════════
# CICLO PRINCIPALE
# ══════════════════════════════════════════════
def ciclo_raccolta(conn, session):
    if not verifica_connessione(session):
        return

    ts       = datetime.now()
    date_to  = datetime.now()
    date_from = date_to - timedelta(hours=INTERVALLO_ORE + GIORNI_OVERLAP * 24)
    df_str   = date_from.strftime("%Y-%m-%d %H:%M:%S")
    dt_str   = date_to.strftime("%Y-%m-%d %H:%M:%S")

    log.info(f"=== Inizio ciclo | Finestra: {df_str} -> {dt_str} ===")

    # Log ciclo
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO log_cicli (ts_inizio, errori) VALUES (%s, 0) RETURNING id",
            (ts,)
        )
        ciclo_id = cur.fetchone()[0]
    conn.commit()

    errori = 0
    nodi_radio = 0
    nodi_batt  = 0

    # 1. STATO RETE
    try:
        r = session.get(f"{BASE_URL}/application/nodes/status",
                        headers=HEADERS, timeout=30)
        if r.status_code == 200:
            d = r.json()
            r2 = session.get(f"{BASE_URL}/gateways", headers=HEADERS,
                             params={"limit": 1, "offset": 0}, timeout=30)
            gw_tot = None
            if r2.status_code == 200:
                d2 = r2.json()
                gw_tot = int(d2.get("totalCount", 0)) if isinstance(d2, dict) else None

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO snapshot_rete
                    (ts_raccolta, nodi_new, nodi_attivi, nodi_timeout, nodi_total, gw_total)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (ts,
                      int(d.get("newCount", 0)),
                      int(d.get("activeCount", 0)),
                      int(d.get("timeoutCount", 0)),
                      int(d.get("totalCount", 0)),
                      gw_tot))
            conn.commit()
            log.info(f"Rete: {d}")
    except Exception as e:
        log.warning(f"Errore snapshot rete: {e}")
        conn.rollback()
        errori += 1

    # 2. ELENCO NODI
    try:
        r = session.get(f"{BASE_URL}/application/nodes/light",
                        headers=HEADERS,
                        params={"limit": 1000, "offset": 0},
                        timeout=60)
        nodi = r.json().get("result", []) if r.status_code == 200 else []
    except Exception as e:
        log.error(f"Errore recupero nodi: {e}")
        errori += 1
        nodi = []

    log.info(f"Nodi da processare: {len(nodi)}")
    log.info(f"Esempio nodo: {nodi[0] if nodi else 'vuoto'}")
    for nodo in nodi:
        dev   = (nodo.get("devEUI") or "").upper()
        app   = (nodo.get("appEUI") or "").upper()
        nome  = nodo.get("name") or ""
        marca = identifica_marca(nome)
        if not dev or not app:
            continue

        # 2a. Pacchetti radio
        try:
            url = f"{BASE_URL}/communicationlog/{app}/{dev}"
            log.debug(f"Chiamata: {url}")
            pkt_salvati = 0
            offset = 0

            while pkt_salvati < MAX_PKT_PER_NODO:
                r = session.get(url, headers=HEADERS,
                                params={"from": df_str, "to": dt_str,
                                        "limit": 50, "offset": offset},
                                timeout=30)
                if r.status_code != 200:
                    break
                pagina = r.json().get("result", [])
                if not pagina:
                    break

                rows = []
                for pkt in pagina:
                    raw = pkt.get("json") or ""
                    try:
                        inner = json.loads(raw)
                    except:
                        continue

                    extra  = inner.get("Extra", {})
                    rxinfo = extra.get("JSONRXINFO", [])
                    data_pkt = pkt.get("date", "")[:19]

                    try:
                        fc = int(extra.get("phyPayloadData", {}).get(
                            "fcounter", extra.get("fCnt", extra.get("fcounter"))))
                    except:
                        fc = None
                    try:
                        sf = int(extra.get("spreadFactor"))
                    except:
                        sf = None

                    gw_list = [e.get("mac", "").upper() for e in rxinfo] if rxinfo \
                              else [g.upper() for g in inner.get("GatewayEUIs", [])]

                    for gw in gw_list:
                        try:
                            rssi_v = float(next(
                                (e.get("rssi") for e in rxinfo if e.get("mac","").upper() == gw),
                                extra.get("rssi", 0)
                            ))
                            snr_v = float(next(
                                (e.get("snr") for e in rxinfo if e.get("mac","").upper() == gw),
                                extra.get("snr", 0)
                            ))
                        except:
                            rssi_v = snr_v = None
                        rows.append((ts, dev, gw, data_pkt, rssi_v, snr_v, sf, fc))

                if rows:
                    with conn.cursor() as cur:
                        execute_values(cur, """
                            INSERT INTO snapshot_radio
                            (ts_raccolta, deveui, gweui, data_pkt, rssi, snr, sf, fcounter)
                            VALUES %s
                            ON CONFLICT DO NOTHING
                        """, rows)
                    conn.commit()
                    pkt_salvati += len(pagina)

                if len(pagina) < 50:
                    break
                offset += 50

            if pkt_salvati > 0:
                nodi_radio += 1

        except Exception as e:
            log.debug(f"  {dev} radio: {e}")
            log.warning(f"  {dev} radio error: {e}")
            conn.rollback()
            errori += 1

        # 2b. Batteria
        if marca and marca in DECODERS:
            try:
                url = f"{BASE_URL}/communicationlog/{app}/{dev}"
                r   = session.get(url, headers=HEADERS,
                                  params={"from": df_str, "to": dt_str,
                                          "limit": 50, "offset": 0},
                                  timeout=30)
                if r.status_code == 200:
                    for pkt in r.json().get("result", []):
                        raw = pkt.get("json") or ""
                        try:
                            inner = json.loads(raw)
                        except:
                            continue
                        payload_hex = inner.get("Payload")
                        if not payload_hex:
                            continue
                        pct, volt = DECODERS[marca](payload_hex)
                        if pct is not None:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO snapshot_batteria
                                    (ts_raccolta, deveui, nome, marca, batteria_pct, volt)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    ON CONFLICT DO NOTHING
                                """, (ts, dev, nome, marca, pct, volt))
                            conn.commit()
                            nodi_batt += 1
                            break
            except Exception as e:
                    log.debug(f"  {dev} batteria: {e}")
                    conn.rollback()  # ← aggiunge questo
                    errori += 1

        time.sleep(PAUSA_TRA_NODI)

    # 3. Aggiorna profilo consolidato
    aggiorna_profilo(conn)

    # 4. Retention
    applica_retention(conn)

    # 5. Aggiorna log ciclo
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE log_cicli
            SET ts_fine=%s, nodi_radio=%s, nodi_batt=%s, errori=%s
            WHERE id=%s
        """, (datetime.now(), nodi_radio, nodi_batt, errori, ciclo_id))
    conn.commit()
    log.info(f"=== Ciclo completato: {nodi_radio} radio, {nodi_batt} batt, {errori} errori ===")


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
def main():
    log.info("Collector PG avviato.")
    log.info(f"Intervallo: ogni {INTERVALLO_ORE} ore")

    conn    = get_conn()
    session = get_session()
    popola_nodi(conn, session)
    while True:
        try:
            ciclo_raccolta(conn, session)
        except Exception as e:
            log.error(f"Errore inaspettato: {e}")
            traceback.print_exc()
            try:
                conn.rollback()  # ← aggiunge questo
            except:
              pass
            conn = get_conn()  # riconnetti se necessario

        prossimo = datetime.now() + timedelta(hours=INTERVALLO_ORE)
        log.info(f"Prossimo ciclo: {prossimo.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(INTERVALLO_ORE * 3600)


if __name__ == "__main__":
    main()