# Gizero Dashboard

Dashboard operativa per il monitoraggio della rete IoT LoRaWAN Gizero.
Sviluppata nell'ambito della tesi magistrale in Informatica presso l'Università di Verona.

## Funzionalità

- **Mappa interattiva** con nodi e gateway della rete LoRaWAN
- **Tre modalità di visualizzazione**: stato radio, batteria, struttura rete
- **Profilo per nodo**: RSSI, SF, SNR, batteria, gateway collegati
- **Tre indici diagnostici**: qualità corrente, fragilità strutturale, tendenza evolutiva
- **Nodi in timeout** visualizzabili separatamente
- **Collector automatico** che aggiorna i dati da ResIOT ogni 12 ore
- **Geocodifica** delle posizioni dei nodi tramite triangolazione RSSI

## Stack tecnologico

| Componente | Tecnologia |
|---|---|
| Frontend | Angular 22 + Leaflet |
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 |
| Collector | Python 3.11 |
| Deploy | Docker Compose + Nginx |

## Struttura del progetto

```
gizero-dashboard/
├── backend/          # API REST FastAPI
│   ├── routers/      # Endpoint: nodi, gateway, batteria, stats
│   ├── sql/          # Schema PostgreSQL
│   └── data/         # File statici (non in Git — vedi Setup)
├── collector/        # Script raccolta dati da ResIOT
├── frontend/         # Applicazione Angular
└── docker-compose.yml
```

## Requisiti

- Docker Engine / Docker Desktop
- Docker Compose v2
- Git

## Setup — Prima installazione

### 1. Clona il repository

```bash
git clone https://github.com/vival02/gizero-dashboard.git
cd gizero-dashboard
```

### 2. Copia i file dati

I file dati non sono inclusi nel repository per motivi di sicurezza.
Copiali nella cartella `backend/data/`:

```bash
mkdir -p backend/data
cp /path/to/usb/data/* backend/data/
```

I file necessari sono:
- `node_positions.json` — coordinate dei nodi
- `gateway_positions.json` — coordinate dei gateway
- `nodi_nomi.json` — nomi dei nodi scaricati da ResIOT

### 3. Configura le variabili d'ambiente

Crea il file `.env` nella root del progetto:

```env
# Database
POSTGRES_DB=gizero
POSTGRES_USER=gizero
POSTGRES_PASSWORD=password_sicura

# ResIOT — inserire il token aziendale
RESIOT_TOKEN=token_aziendale_gizero
RESIOT_BASE_URL=https://gizero.resiot.io/api
```

### 4. Avvia il sistema

```bash
docker compose up -d --build
```

### 5. Verifica

```bash
docker compose ps
```

Tutti e quattro i container devono essere in stato `running`:
- `gizero_db` — PostgreSQL
- `gizero_backend` — FastAPI
- `gizero_collector` — Collector ResIOT
- `gizero_frontend` — Angular + Nginx

La dashboard è disponibile su `http://localhost` o `http://IP_DEL_SERVER`.

> **Nota**: al primo avvio il collector impiega circa 15 minuti per completare il primo ciclo di raccolta dati. La mappa apparirà popolata al termine del ciclo.

## Aggiornamenti

```bash
git pull
docker compose up -d --build
```

## Comandi utili

```bash
# Log di tutti i container
docker compose logs -f

# Log del solo collector
docker compose logs -f collector

# Log del solo backend
docker compose logs -f backend

# Riavviare un container
docker compose restart backend

# Fermare tutto
docker compose down

# Fermare tutto e cancellare il database
docker compose down -v
```

## Architettura

```
ResIOT API
    ↓  ogni 12h
Collector (Python)
    ↓  scrive
PostgreSQL
    ↓  legge
FastAPI  →  REST API  →  Angular + Leaflet
```

## Note per la produzione

- Il `RESIOT_TOKEN` nel `.env` deve essere un token aziendale dedicato, non personale
- La porta `5432` (PostgreSQL) è esposta solo per debug — in produzione può essere chiusa nel `docker-compose.yml`
- Per aggiornamenti remoti configurare accesso SSH al server e usare `git pull && docker compose up -d --build`

## Sviluppata da

**Camilla Vivaldi** — Tesi Magistrale in Informatica
Università di Verona — A.A. 2025/2026
Relatore: Prof. Davide Quaglia
Correlatore aziendale: Sandro Rizzato (ABS Computers srl)
