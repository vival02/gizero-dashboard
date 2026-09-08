import { Component, ChangeDetectorRef } from '@angular/core';
import { Map } from './components/map/map';
import { NodePanel } from './components/node-panel/node-panel';
import { Header, LayerVisibility } from './components/header/header';
import { SideMenu, Modalita } from './components/side-menu/side-menu';

@Component({
  selector: 'app-root',
  imports: [Map, NodePanel, Header, SideMenu],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  menuAperto = false;
  modalita: Modalita = 'radio';
  nodoSelezionato: any = null;
  layers: LayerVisibility = { nodi: true, gateway: true };

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
}