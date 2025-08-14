import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Prompts } from './prompts';

describe('Prompts', () => {
  let component: Prompts;
  let fixture: ComponentFixture<Prompts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [Prompts]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Prompts);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
