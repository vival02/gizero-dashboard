import { Component, Input, Output, EventEmitter, OnChanges, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Nodo } from '../../services/api';

@Component({
  selector: 'app-node-panel',
  imports: [CommonModule],
  templateUrl: './node-panel.html',
  styleUrl: './node-panel.scss'
})
export class NodePanel implements OnChanges {
  @Input() nodo: Nodo | null = null;
  @Output() chiudi = new EventEmitter<void>();

  storico: any[] = [];
  caricamento = false;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}
  gateway: any[] = [];
  ngOnChanges() {
    if (this.nodo) {
      this.caricamento = true;
      this.api.getNodo(this.nodo.deveui).subscribe({
        next: res => {
          this.storico = res.storico;
          this.gateway  = res.gateway || [];
          this.caricamento = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.caricamento = false;
          this.cdr.detectChanges();
        }
      });
    }
  }

  get aperto(): boolean {
    return this.nodo !== null;
  }

  indiceBar(valore: number | null): number {
    return Math.round((valore ?? 0) * 100);
  }

  indiceColore(valore: number | null): string {
    const v = valore ?? 0;
    if (v >= 0.7) return '#ef5350';
    if (v >= 0.4) return '#ffa726';
    return '#66bb6a';
  }

  statoColore(stato: string): string {
    if (stato === 'CRITICO')    return '#E53935';
    if (stato === 'ATTENZIONE') return '#FB8C00';
    return '#8DC63F';
  }

  battColore(pct: number | null): string {
    if (pct == null) return '#B0BEC5';
    if (pct < 10)   return '#E53935';
    if (pct < 20)   return '#FF5722';
    if (pct < 50)   return '#FB8C00';
    return '#8DC63F';
  }
}