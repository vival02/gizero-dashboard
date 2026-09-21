import requests
import psycopg2
import os
from psycopg2.extras import execute_values

BASE_URL = os.environ.get("RESIOT_BASE_URL", "https://gizero.resiot.io/api")
TOKEN    = os.environ.get("RESIOT_TOKEN", "")
HEADERS  = {"Accept": "application/json", "Grpc-Metadata-Authorization": TOKEN}

conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "gizero_db"),
    dbname=os.environ.get("POSTGRES_DB", "gizero"),
    user=os.environ.get("POSTGRES_USER", "gizero"),
    password=os.environ.get("POSTGRES_PASSWORD", "")
)

r = requests.get(
    f"{BASE_URL}/application/nodes",
    headers=HEADERS,
    params={"limit": 1000, "offset": 0}
)
nodi = r.json().get("result", [])
print(f"Nodi trovati: {len(nodi)}")

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