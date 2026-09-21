import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RisultatiSimulazione } from './risultati-simulazione';

describe('RisultatiSimulazione', () => {
  let component: RisultatiSimulazione;
  let fixture: ComponentFixture<RisultatiSimulazione>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RisultatiSimulazione],
    }).compileComponents();

    fixture = TestBed.createComponent(RisultatiSimulazione);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
