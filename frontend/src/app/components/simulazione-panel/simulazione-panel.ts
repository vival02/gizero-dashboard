import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface GatewaySimulato {
  nome: string;
  lat: number;
  lon: number;
}

export interface RisultatoSimulazione {
  nodi_migliorati: { deveui: string; nome: string; iqt_prima: number; iqt_dopo: number; gateway: string }[];
  riepilogo: { nodi_migliorati: number; nodi_critici_risolti: number; nodi_ridondanza_aggiunta: number };
  testo_raccomandazione: string;
}

@Component({
  selector: 'app-simulazione-panel',
  imports: [CommonModule, FormsModule],
  templateUrl: './simulazione-panel.html',
  styleUrl: './simulazione-panel.scss'
})
export class SimulazionePanel {
  @Input() nuoveCoordinate: {lat: number, lon: number} | null = null;
  @Output() gatewayListChange = new EventEmitter<GatewaySimulato[]>();
  @Output() reset = new EventEmitter<void>();
  @Output() risultati = new EventEmitter<RisultatoSimulazione>();

  gateway: GatewaySimulato[] = [];
  caricamento = false;
  risultatoCorrente: RisultatoSimulazione | null = null;

  ngOnChanges() {
    if (this.nuoveCoordinate) {
      this.aggiungiGateway(this.nuoveCoordinate.lat, this.nuoveCoordinate.lon);
    }
  }

  aggiungiGateway(lat: number, lon: number) {
    const n = this.gateway.length + 1;
    this.gateway.push({
      nome: `GW Simulato ${n}`,
      lat: parseFloat(lat.toFixed(5)),
      lon: parseFloat(lon.toFixed(5)),
    });
    this.gatewayListChange.emit(this.gateway);
  }

  eliminaGateway(i: number) {
    this.gateway.splice(i, 1);
    this.gateway.forEach((g, idx) => {
      if (g.nome.startsWith('GW Simulato')) g.nome = `GW Simulato ${idx + 1}`;
    });
    this.gatewayListChange.emit(this.gateway);
  }

  avviaSimulazione() {
    if (this.gateway.length === 0) return;
    this.caricamento = true;

    // Mock temporaneo — da sostituire con vera chiamata API
    setTimeout(() => {
      this.risultatoCorrente = {
        nodi_migliorati: [],
        riepilogo: { nodi_migliorati: 0, nodi_critici_risolti: 0, nodi_ridondanza_aggiunta: 0 },
        testo_raccomandazione: 'Backend simulazione non ancora collegato. I risultati appariranno qui una volta implementato il modello LDPL.'
      };
      this.caricamento = false;
      this.risultati.emit(this.risultatoCorrente);
    }, 1500);
  }

  resetSimulazione() {
    this.gateway = [];
    this.risultatoCorrente = null;
    this.gatewayListChange.emit([]);
    this.reset.emit();
  }
}