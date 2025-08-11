import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PromptAdd } from './prompt-add';

describe('PromptAdd', () => {
  let component: PromptAdd;
  let fixture: ComponentFixture<PromptAdd>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PromptAdd]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PromptAdd);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
