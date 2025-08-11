import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MyPrompts } from './my-prompts';

describe('MyPrompts', () => {
  let component: MyPrompts;
  let fixture: ComponentFixture<MyPrompts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MyPrompts]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MyPrompts);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
