import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TotpVerification } from './totp-verification';

describe('TotpVerification', () => {
  let component: TotpVerification;
  let fixture: ComponentFixture<TotpVerification>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TotpVerification]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TotpVerification);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
