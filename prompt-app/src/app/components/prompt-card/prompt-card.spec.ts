import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PromptCard } from './prompt-card';

describe('PromptCard', () => {
  let component: PromptCard;
  let fixture: ComponentFixture<PromptCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PromptCard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PromptCard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
