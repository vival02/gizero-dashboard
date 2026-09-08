import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Nodo {
  deveui: string;
  stato: 'CRITICO' | 'ATTENZIONE' | 'OK' | 'TIMEOUT';
  rssi_medio: number;
  sf_medio: number;
  snr_medio: number;
  giorni_batteria: number | null;
  batteria_pct: number | null;
  indice_qualita: number | null;
  indice_fragilita: number | null;
  indice_tendenza: number | null;
  n_gateway: number;
  lat: number | null;
  lon: number | null;
  nome: string;
  marca: string;
  classificazione: string;
  trend: string;
}

export interface Gateway {
  gweui: string;
  nome: string;
  lat: number;
  lon: number;
  rssi_medio: number;
  sf_medio: number;
  n_nodi: number;
  n_pacchetti: number;
  ultimo_contatto: string;
  attivo: boolean;
}

export interface Stats {
  nodi: {
    totale: number;
    attivi: number;
    critici: number;
    attenzione: number;
    ok: number;
  };
  gateway: {
    totale: number;
  };
  batteria_critici: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = '/api';

  constructor(private http: HttpClient) {}

  getNodi(stato?: string): Observable<{ nodi: Nodo[] }> {
    const url = stato
      ? `${this.base}/nodi?stato=${stato}`
      : `${this.base}/nodi`;
    return this.http.get<{ nodi: Nodo[] }>(url);
  }

getNodo(deveui: string): Observable<{ profilo: Nodo; storico: any[]; gateway: any[] }> {
  return this.http.get<{ profilo: Nodo; storico: any[]; gateway: any[] }>(
    `${this.base}/nodi/${deveui}`
  );
}

  getGateway(): Observable<{ gateway: Gateway[] }> {
    return this.http.get<{ gateway: Gateway[] }>(`${this.base}/gateway`);
  }

  getStats(): Observable<Stats> {
    return this.http.get<Stats>(`${this.base}/stats/`);
  }
}