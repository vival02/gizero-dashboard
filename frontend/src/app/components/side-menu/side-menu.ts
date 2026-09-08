import { Component, EventEmitter,Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type Modalita = 'radio' | 'batteria' | 'struttura';

@Component({
  selector: 'app-side-menu',
  imports: [CommonModule],
  templateUrl: './side-menu.html',
  styleUrl: './side-menu.scss'
})
export class SideMenu {
  @Output() modalitaChange = new EventEmitter<Modalita>();
@Input() aperto = false;
  modalitaAttiva: Modalita = 'radio';

  voci = [
    {
      id: 'radio' as Modalita,
      label: 'STATO RADIO',
      descrizione: 'RSSI e Spreading Factor'
    },
    {
      id: 'batteria' as Modalita,
      label: 'BATTERIA',
      descrizione: 'Livello e vita residua'
    },
    {
      id: 'struttura' as Modalita,
      label: 'STRUTTURA RETE',
      descrizione: 'Ridondanza e fragilità'
    }
  ];

  seleziona(m: Modalita) {
    this.modalitaAttiva = m;
    this.modalitaChange.emit(m);
  }
}