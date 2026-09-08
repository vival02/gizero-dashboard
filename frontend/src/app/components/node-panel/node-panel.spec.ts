import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NodePanel } from './node-panel';

describe('NodePanel', () => {
  let component: NodePanel;
  let fixture: ComponentFixture<NodePanel>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NodePanel],
    }).compileComponents();

    fixture = TestBed.createComponent(NodePanel);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
