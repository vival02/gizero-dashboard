import {
  Component, Input, Output, EventEmitter,
  OnChanges, ElementRef, ViewChild, afterNextRender, NgZone, ChangeDetectorRef
} from '@angular/core';
import * as L from 'leaflet';
(window as any).L = L;
import { ApiService, Nodo, Gateway } from '../../services/api';
import { LayerVisibility } from '../header/header';

export type Modalita = 'radio' | 'batteria' | 'struttura';

const GRIGIO_TIMEOUT = '#607D8B';
const GRIGIO_NO_BATT = '#B0BEC5';

@Component({
  selector: 'app-map',
  templateUrl: './map.html',
  styleUrl: './map.scss'
})
export class Map implements OnChanges {
  @Input() modalita: Modalita = 'radio';
  @Input() layers: LayerVisibility = { nodi: true, gateway: true };
  @Input() mostraTimeout = false;
  @Output() nodoSelezionato = new EventEmitter<Nodo>();

  @ViewChild('mapContainer', { static: true }) mapContainer!: ElementRef;

  private map!: L.Map;
  private gatewayLayer = L.layerGroup();
  private popupTimeout: any;
  private nodoCluster!: any;
  nodi: Nodo[] = [];
  gateway: Gateway[] = [];
  caricamento = true;
  
constructor(private api: ApiService, private zone: NgZone, private cdr: ChangeDetectorRef) {
    afterNextRender(async () => {
      await import('leaflet.markercluster');
      this.inizializzaMappa();
      this.caricaDati();
    });
  }

  ngOnChanges() {
    if (this.map) {
      this.aggiornaVisibilita();
      this.aggiornaMarker();
    }
  }

  private inizializzaMappa() {
    this.map = L.map(this.mapContainer.nativeElement, {
      center: [45.4654, 10.9997],
      zoom: 11,
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(this.map);

    this.nodoCluster = (L as any).markerClusterGroup({
      showCoverageOnHover: false,
      maxClusterRadius: 40,
      spiderfyOnMaxZoom: false,
      disableClusteringAtZoom: 13,
      spiderfy: false,
      zoomToBoundsOnClick: true,
      iconCreateFunction: (cluster: any) => {
        const markers = cluster.getAllChildMarkers();
        let critici = 0, attenzione = 0, ok = 0, timeout = 0;
        markers.forEach((m: any) => {
          const colore = m.options?.fillColor;
          if (colore === '#E53935')          critici++;
          else if (colore === '#FB8C00')     attenzione++;
          else if (colore === GRIGIO_TIMEOUT) timeout++;
          else ok++;
        });

        let colore = '#8DC63F';
        if (critici > attenzione && critici > ok)                             colore = '#E53935';
        else if (attenzione > ok)                                             colore = '#FB8C00';
        else if (timeout > ok && timeout > critici && timeout > attenzione)   colore = GRIGIO_TIMEOUT;

        const count = cluster.getChildCount();
        return L.divIcon({
          html: `<div style="
            width:30px; height:30px; border-radius:50%;
            background:${colore}; color:white;
            font-size:13px; font-weight:700;
            display:flex; align-items:center; justify-content:center;
            border:2px solid white;
            box-shadow:0 2px 6px rgba(0,0,0,0.25);
          ">${count}</div>`,
          className: '',
          iconSize: [36, 36],
        });
      }
    });

    this.nodoCluster.addTo(this.map);
    this.gatewayLayer.addTo(this.map);
  }

  private caricaDati() {
    this.api.getNodi().subscribe(res => {
      this.nodi = res.nodi.filter(n => n.lat && n.lon);
      this.api.getGateway().subscribe(res2 => {
        this.gateway = res2.gateway.filter(g => g.lat && g.lon);
        this.caricamento = false;
        this.cdr.detectChanges();
        this.aggiornaMarker();
      });
    });
  }

  private aggiornaVisibilita() {
    if (this.layers.nodi) {
      this.map.addLayer(this.nodoCluster);
    } else {
      this.map.removeLayer(this.nodoCluster);
    }
    if (this.layers.gateway) {
      this.map.addLayer(this.gatewayLayer);
    } else {
      this.map.removeLayer(this.gatewayLayer);
    }
  }

  private aggiornaMarker() {
    this.nodoCluster.clearLayers();
    this.gatewayLayer.clearLayers();
    this.disegnaNodi();
    this.disegnaGateway();
  }

  // ── Colori ────────────────────────────────────────────────

  private coloreNodo(nodo: Nodo): string {
    if (nodo.stato === 'TIMEOUT') return GRIGIO_TIMEOUT;

    switch (this.modalita) {
      case 'radio':
        if (nodo.stato === 'CRITICO')    return '#E53935';
        if (nodo.stato === 'ATTENZIONE') return '#FB8C00';
        return '#8DC63F';

      case 'batteria':
        if (nodo.batteria_pct == null) return GRIGIO_NO_BATT;
        if (nodo.batteria_pct < 10)   return '#E53935';
        if (nodo.batteria_pct < 20)   return '#FF5722';
        if (nodo.batteria_pct < 50)   return '#FB8C00';
        return '#8DC63F';

      case 'struttura':
        const gw = nodo.n_gateway ?? 0;
        if (gw === 0) return GRIGIO_TIMEOUT;
        if (gw === 1) return '#E53935';
        return '#8DC63F';
    }
  }

  private coloreGateway(gw: Gateway): string {
    if (!gw.attivo)            return GRIGIO_TIMEOUT;
    if (gw.rssi_medio <= -105) return '#E53935';
    if (gw.rssi_medio <= -95)  return '#FB8C00';
    return '#8DC63F';
  }

  // ── Disegno ───────────────────────────────────────────────

  private disegnaNodi() {
    for (const nodo of this.nodi) {
      if (nodo.stato === 'TIMEOUT' && !this.mostraTimeout) continue;

      const colore = this.coloreNodo(nodo);
      const marker = L.circleMarker([nodo.lat!, nodo.lon!], {
        radius: 7,
        fillColor: colore,
        color: '#fff',
        weight: 1.5,
        fillOpacity: 0.9,
      });

      marker.bindPopup(this.popupNodo(nodo), {
        closeButton: false,
        className: 'popup-leggero'
        
      });

      marker.on('mouseover', () => {
        clearTimeout(this.popupTimeout);
        marker.openPopup();
      });
      marker.on('mouseout', () => {
        const m = marker;
        this.popupTimeout = setTimeout(() => m.closePopup(), 800);
      });
      marker.on('click', () => this.zone.run(() => this.nodoSelezionato.emit(nodo)));

      this.nodoCluster.addLayer(marker);
    }
  }

  private disegnaGateway() {
    for (const gw of this.gateway) {
      const icon = L.divIcon({
        className: '',
        html: `<svg width="22" height="22" viewBox="0 0 22 22">
                 <polygon points="11,2 21,20 1,20"
                   fill="#1565C0"
                   fill-opacity="0.85"
                   stroke="#ffffff"
                   stroke-width="1.5"
                   stroke-linejoin="round"/>
               </svg>`,
        iconSize: [22, 22],
        iconAnchor: [11, 20],
      });

      const marker = L.marker([gw.lat, gw.lon], { icon });
      marker.bindPopup(this.popupGateway(gw), {
        closeButton: false,
        className: 'popup-leggero'
      });

      marker.on('mouseover', () => {
        clearTimeout(this.popupTimeout);
        marker.openPopup();
      });
      marker.on('mouseout', () => {
        const m = marker;
        this.popupTimeout = setTimeout(() => m.closePopup(), 400);
      });

      this.gatewayLayer.addLayer(marker);
    }
  }

  // ── Popup ─────────────────────────────────────────────────

  private popupNodo(n: Nodo): string {
    const batt = n.batteria_pct != null ? `${n.batteria_pct.toFixed(0)}%` : 'N/D';
    const nome = n.nome ? `<div class="popup-nome">${n.nome}</div>` : '';
    const rssi = n.stato !== 'TIMEOUT' ? `<div class="popup-row">RSSI <b>${n.rssi_medio.toFixed(0)} dBm</b></div>` : '';
    const sf   = n.stato !== 'TIMEOUT' ? `<div class="popup-row">SF <b>${n.sf_medio.toFixed(1)}</b></div>` : '';
    return `
      <div class="popup-content">
        ${nome}
        <div class="popup-eui">${n.deveui}</div>
        ${rssi}
        ${sf}
        <div class="popup-row">Batteria <b>${batt}</b></div>
        <div class="popup-stato stato-${n.stato.toLowerCase()}">${n.stato}</div>
      </div>`;
  }

  private popupGateway(g: Gateway): string {
    return `
      <div class="popup-content">
        <div class="popup-nome">${g.nome}</div>
        <div class="popup-eui">${g.gweui}</div>
      </div>`;
  }
}