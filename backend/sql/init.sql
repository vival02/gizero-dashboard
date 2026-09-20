-- ============================================================
--  GIZERO DASHBOARD — Schema PostgreSQL
--  Fase 1: tabelle principali + retention policy
-- ============================================================

-- Nodi
CREATE TABLE IF NOT EXISTS nodi (
    deveui          VARCHAR(16) PRIMARY KEY,
    nome            VARCHAR,
    marca           VARCHAR,
    attivo          BOOLEAN DEFAULT TRUE,
    tenant_id       INTEGER DEFAULT 1,   -- multi-tenant futuro
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Gateway
CREATE TABLE IF NOT EXISTS gateway (
    gweui           VARCHAR(16) PRIMARY KEY,
    nome            VARCHAR,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION,
    attivo          BOOLEAN DEFAULT TRUE,
    tenant_id       INTEGER DEFAULT 1,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Snapshot radio (dati grezzi — retention 14 giorni)
CREATE TABLE IF NOT EXISTS snapshot_radio (
    id              SERIAL PRIMARY KEY,
    ts_raccolta     TIMESTAMP NOT NULL,
    deveui          VARCHAR(16),
    gweui           VARCHAR(16),
    data_pkt        TIMESTAMP,
    rssi            DOUBLE PRECISION,
    snr             DOUBLE PRECISION,
    sf              INTEGER,
    fcounter        INTEGER
);
CREATE INDEX IF NOT EXISTS idx_radio_ts    ON snapshot_radio(ts_raccolta);
CREATE INDEX IF NOT EXISTS idx_radio_dev   ON snapshot_radio(deveui);

-- Snapshot batteria (retention 30 giorni)
CREATE TABLE IF NOT EXISTS snapshot_batteria (
    id              SERIAL PRIMARY KEY,
    ts_raccolta     TIMESTAMP NOT NULL,
    deveui          VARCHAR(16),
    nome            VARCHAR,
    marca           VARCHAR,
    batteria_pct    DOUBLE PRECISION,
    volt            DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_batt_ts     ON snapshot_batteria(ts_raccolta);
CREATE INDEX IF NOT EXISTS idx_batt_dev    ON snapshot_batteria(deveui);

-- Riepilogo giornaliero (retention 1 anno)
CREATE TABLE IF NOT EXISTS daily_summary (
    data            DATE NOT NULL,
    deveui          VARCHAR(16) NOT NULL,
    rssi_medio      DOUBLE PRECISION,
    sf_medio        DOUBLE PRECISION,
    snr_medio       DOUBLE PRECISION,
    n_pacchetti     INTEGER,
    sf12_ratio      DOUBLE PRECISION,
    n_gateway       INTEGER,
    PRIMARY KEY (data, deveui)
);

-- Profilo consolidato (1 riga per nodo, sempre aggiornata)
CREATE TABLE IF NOT EXISTS profilo_nodi (
    deveui              VARCHAR(16) PRIMARY KEY,
    ts_aggiornamento    TIMESTAMP DEFAULT NOW(),
    stato               VARCHAR(20),    -- CRITICO / ATTENZIONE / OK
    rssi_medio          DOUBLE PRECISION,
    sf_medio            DOUBLE PRECISION,
    snr_medio           DOUBLE PRECISION,
    giorni_batteria     INTEGER,
    batteria_pct        DOUBLE PRECISION,
    indice_qualita      DOUBLE PRECISION,
    indice_fragilita    DOUBLE PRECISION,
    indice_tendenza     DOUBLE PRECISION,
    n_gateway           INTEGER,
    lat                 DOUBLE PRECISION,
    lon                 DOUBLE PRECISION
);

-- Stato rete (snapshot globale ogni ciclo collector)
CREATE TABLE IF NOT EXISTS snapshot_rete (
    id              SERIAL PRIMARY KEY,
    ts_raccolta     TIMESTAMP DEFAULT NOW(),
    nodi_total      INTEGER,
    nodi_attivi     INTEGER,
    nodi_timeout    INTEGER,
    nodi_new        INTEGER,
    gw_total        INTEGER,
    nodi_critici    INTEGER,
    nodi_attenzione INTEGER,
    nodi_ok         INTEGER
);

-- Log cicli collector
CREATE TABLE IF NOT EXISTS log_cicli (
    id              SERIAL PRIMARY KEY,
    ts_inizio       TIMESTAMP,
    ts_fine         TIMESTAMP,
    nodi_radio      INTEGER,
    nodi_batt       INTEGER,
    errori          INTEGER DEFAULT 0,
    note            TEXT
);
