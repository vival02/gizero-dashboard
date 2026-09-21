import { Component, ChangeDetectorRef } from '@angular/core';
import { Map } from './components/map/map';
import { NodePanel } from './components/node-panel/node-panel';
import { Header, LayerVisibility } from './components/header/header';
import { SideMenu, Modalita } from './components/side-menu/side-menu';
import { SimulazionePanel } from './components/simulazione-panel/simulazione-panel';
@Component({
  selector: 'app-root',
  imports: [Map, NodePanel, Header, SideMenu, SimulazionePanel],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  menuAperto = false;
  modalita: Modalita = 'radio';
  nodoSelezionato: any = null;
  layers: LayerVisibility = { nodi: true, gateway: true };
  gatewaySimulati: any[] = [];
  nodiMigliorati: string[] = [];
  ultimoClick: {lat: number, lon: number} | null = null;
  constructor(private cdr: ChangeDetectorRef) {}

  onMenuToggle() {
    this.menuAperto = !this.menuAperto;
    this.cdr.detectChanges();
    console.log('menuAperto:', this.menuAperto);
  }
  mostraTimeout = false;

onTimeoutChange(v: boolean) {
  this.mostraTimeout = v;
}
  onModalitaChange(m: Modalita) {
    this.modalita = m;
if (m === 'batteria') {
  this.layers = { nodi: true, gateway: false };
} else if (m === 'simulazione') {
  this.layers = { nodi: true, gateway: true };
} else {
  this.layers = { nodi: true, gateway: true };
}
  }

  onNodoSelezionato(nodo: any) {
    this.nodoSelezionato = nodo;
  }

  onLayerChange(l: LayerVisibility) {
    this.layers = { ...l };
  }

  onMapClick() {
    if (this.menuAperto) {
      this.menuAperto = false;
      this.cdr.detectChanges();
    }
  }
  onMappaCliccata(coords: {lat: number, lon: number}) {
  if (this.modalita === 'simulazione') {
    this.ultimoClick = coords;
  }
}

onGatewayListChange(lista: any[]) {
  this.gatewaySimulati = [...lista];
  this.ultimoClick = null;
}

onSimulazioneReset() {
  this.gatewaySimulati = [];
  this.nodiMigliorati = [];
  this.ultimoClick = null;
}

onRisultatiSimulazione(risultati: any) {
  this.nodiMigliorati = risultati.nodi_migliorati.map((n: any) => n.deveui);
}
  onGatewayAggiunto(gateway: any) {
  // gestito dal componente simulazione-panel
}

}