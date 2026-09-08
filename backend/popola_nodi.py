import requests
import psycopg2
from psycopg2.extras import execute_values

BASE_URL = "https://gizero.resiot.io/api"
TOKEN    = "0d126be8225daa1a384f980cfc79f952"
HEADERS  = {"Accept": "application/json", "Grpc-Metadata-Authorization": TOKEN}

conn = psycopg2.connect(
    host="localhost", dbname="gizero",
    user="gizero", password="cambia_questa_password"
)

# Scarica tutti i nodi da ResIOT
r = requests.get(
    f"{BASE_URL}/application/nodes",
    headers=HEADERS,
    params={"limit": 1000, "offset": 0}
)
nodi = r.json().get("result", [])
print(f"Nodi trovati: {len(nodi)}")

# Salva in tabella nodi
records = []
for n in nodi:
    dev  = n.get("devEUI", "").upper().strip()
    nome = n.get("name", "").strip()
    if dev:
        records.append((dev, nome, True))

with conn.cursor() as cur:
    execute_values(cur, """
        INSERT INTO nodi (deveui, nome, attivo)
        VALUES %s
        ON CONFLICT (deveui) DO UPDATE SET nome = EXCLUDED.nome
    """, records)
conn.commit()
conn.close()
print(f"Salvati {len(records)} nodi")