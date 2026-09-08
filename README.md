# Gizero Dashboard

Dashboard di monitoraggio rete LoRaWAN Gizero.

## Stack
- **Frontend**: Angular + Leaflet (Nginx)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Collector**: Script Python che scarica dati da ResIOT ogni 12h

## Requisiti
- Docker Desktop / Docker Engine
- Docker Compose v2

## Prima installazione

1. Clona o copia la cartella del progetto sul server
2. Copia i file dati nella cartella `backend/data/`:
   - `node_positions.json`
   - `gateway_positions.json`
   - `nodi_nomi.json`
3. Crea il file `.env` nella root con le credenziali:
POSTGRES_DB=gizero
POSTGRES_USER=gizero
POSTGRES_PASSWORD=password_sicura
RESIOT_TOKEN=token_resiot_aziendale
RESIOT_BASE_URL=https://gizero.resiot.io/api


4. Avvia tutto:

```bash
docker compose up -d --build
```

5. La dashboard è disponibile su `http://localhost` (o IP del server)

## Aggiornamenti

```bash
git pull
docker compose up -d --build
```

## Comandi utili

```bash
# Vedere i log
docker compose logs -f

# Vedere solo il collector
docker compose logs -f collector

# Riavviare un singolo container
docker compose restart backend

# Fermare tutto
docker compose down

# Fermare tutto e cancellare i dati
docker compose down -v
```

## Note
- Il collector gira automaticamente ogni 12h
- Al primo avvio ci vogliono ~15 minuti per il primo ciclo completo
- Il token ResIOT va sostituito con quello aziendale prima del deploy
- La porta 5432 (PostgreSQL) è esposta solo per debug — in produzione può essere chiusa