import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FavoritePrompts } from './favorite-prompts';

describe('FavoritePrompts', () => {
  let component: FavoritePrompts;
  let fixture: ComponentFixture<FavoritePrompts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [FavoritePrompts]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FavoritePrompts);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
