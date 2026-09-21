import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SimulazionePanel } from './simulazione-panel';

describe('SimulazionePanel', () => {
  let component: SimulazionePanel;
  let fixture: ComponentFixture<SimulazionePanel>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SimulazionePanel],
    }).compileComponents();

    fixture = TestBed.createComponent(SimulazionePanel);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
