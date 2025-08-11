// src/app/pages/profile/profile.ts

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidatorFn, FormControl } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Observable, of } from 'rxjs';

// Şifrelerin eşleşip eşleşmediğini kontrol eden özel validator fonksiyonu
export function passwordMatchValidator(
  controlName: string,
  checkControlName: string
): ValidatorFn {
  return (formGroup: AbstractControl) => {
    const control = formGroup.get(controlName);
    const checkControl = formGroup.get(checkControlName);

    if (!control || !checkControl || (checkControl.errors && !checkControl.errors['mismatch'])) {
      return null;
    }

    if (control.value !== checkControl.value) {
      checkControl.setErrors({ mismatch: true });
      return { mismatch: true };
    } else {
      checkControl.setErrors(null);
      return null;
    }
  };
}

@Component({
  selector: 'app-profile',
  templateUrl: './profile.html',
  standalone: false,
  styleUrls: ['./profile.css']
})
export class Profile implements OnInit {
  passwordChangeForm!: FormGroup;
  deletePasswordControl = new FormControl('', Validators.required);

  currentUserUsername$: Observable<string | null>;
  currentUserEmail$: Observable<string | null> = of(null);
  currentUserFirstName$: Observable<string | null> = of(null);
  currentUserLastName$: Observable<string | null> = of(null);
  currentUserId: number | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.currentUserUsername$ = this.authService.currentUserUsername$;
  }

  ngOnInit(): void {
    this.passwordChangeForm = this.fb.group({
      current_password: ['', Validators.required],
      new_password: ['', [Validators.required, Validators.minLength(8)]],
      new_password_confirm: ['', Validators.required]
    }, { validators: passwordMatchValidator('new_password', 'new_password_confirm') });

    this.authService.getMe().subscribe({
      next: (user) => {
        if (user) {
          this.currentUserId = user.id;
          this.currentUserEmail$ = of(user.email || null);
          this.currentUserFirstName$ = of(user.first_name || null);
          this.currentUserLastName$ = of(user.last_name || null);
        } else {
          this.snackBar.open('Kullanıcı bilgileri yüklenemedi. Lütfen tekrar giriş yapın.', 'Kapat', { duration: 3000 });
          this.authService.logout();
        }
      },
      error: (err) => {
        console.error('Kullanıcı bilgileri çekilemedi:', err);
        this.snackBar.open('Kullanıcı bilgileri yüklenirken hata oluştu.', 'Kapat', { duration: 3000 });
        this.authService.logout();
      }
    });
  }

  changePassword(): void {
    if (this.passwordChangeForm.valid) {
      const { current_password, new_password } = this.passwordChangeForm.value;
      this.authService.changePassword(current_password, new_password).subscribe({
        next: () => {
          this.snackBar.open('Şifreniz başarıyla değiştirildi!', 'Kapat', { duration: 3000 });
          this.passwordChangeForm.reset();
        },
        error: (err) => {
          console.error('Şifre değiştirme hatası:', err);
          const errorMessage = err.error?.detail || 'Şifre değiştirme başarısız.';
          this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
        }
      });
    } else {
      this.passwordChangeForm.markAllAsTouched();
      this.snackBar.open('Lütfen formdaki hataları düzeltin.', 'Kapat', { duration: 3000 });
    }
  }

  deleteAccount(): void {
    if (this.deletePasswordControl.invalid) {
      this.deletePasswordControl.markAsTouched();
      this.snackBar.open('Hesabınızı silmek için şifrenizi girmeniz gerekli.', 'Kapat', { duration: 3000 });
      return;
    }

    const password = this.deletePasswordControl.value!;

    // API'nin beklediği gibi, ID'yi ve şifreyi birlikte gönderiyoruz.
    if (confirm('Hesabınızı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!')) {
      if (this.currentUserId !== null) {
        this.authService.deleteUserWithPassword(this.currentUserId, password).subscribe({
          next: () => {
            this.snackBar.open('Hesabınız başarıyla silindi.', 'Kapat', { duration: 3000 });
            this.authService.logout();
          },
          error: (err) => {
            console.error('Hesap silme hatası:', err);
            const errorMessage = err.error?.detail || 'Hesap silme başarısız. Lütfen şifrenizi kontrol edin.';
            this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
          }
        });
      } else {
        this.snackBar.open('Kullanıcı bilgisi alınamadı. Lütfen sayfayı yenileyin.', 'Kapat', { duration: 3000 });
      }
    }
  }

  logout(): void {
    this.authService.logout();
    this.snackBar.open('Başarıyla çıkış yapıldı.', 'Kapat', { duration: 2000 });
  }
}
