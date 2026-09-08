import { Component, OnInit, Output,Input , EventEmitter,ChangeDetectorRef   } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, Stats } from '../../services/api';

export interface LayerVisibility {
  nodi: boolean;
  gateway: boolean;
}

@Component({
  selector: 'app-header',
  imports: [CommonModule],
  templateUrl: './header.html',
  styleUrl: './header.scss'
})
export class Header implements OnInit {
  @Output() layerChange = new EventEmitter<LayerVisibility>();
  @Input() layers: LayerVisibility = { nodi: true, gateway: true };
  @Output() menuToggle = new EventEmitter<void>();
  @Output() timeoutChange = new EventEmitter<boolean>();
mostraTimeout = false;

toggleTimeout() {
  this.mostraTimeout = !this.mostraTimeout;
  this.timeoutChange.emit(this.mostraTimeout);
}
  stats: Stats | null = null;
  mostraNodi = true;
  mostraGateway = true;
toggleMenu() {
  console.log('hamburger cliccato');
  this.menuToggle.emit();
}
  constructor(private api: ApiService, private cdr: ChangeDetectorRef ) {}
  ngOnInit() {
    this.api.getStats().subscribe(s => {
      this.stats = s;
      this.cdr.detectChanges();
    });
  }

 toggleNodi() {
    this.mostraNodi = !this.mostraNodi;
    this.layerChange.emit({ nodi: this.mostraNodi, gateway: this.mostraGateway });
  }

  toggleGateway() {
    this.mostraGateway = !this.mostraGateway;
    this.layerChange.emit({ nodi: this.mostraNodi, gateway: this.mostraGateway });
  }
}