// src/app/pages/login/login.component.ts

import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { HttpErrorResponse } from '@angular/common/http'; // HttpErrorResponse hala genel hata yakalamak için gerekli
import { first } from 'rxjs/operators';

@Component({
  selector: 'app-login',
  standalone: false,
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class Login implements OnInit {
  loginForm!: FormGroup;
  isSubmitting: boolean = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      this.snackBar.open('Lütfen kullanıcı adı ve şifrenizi girin.', 'Kapat', { duration: 3000 });
      return;
    }

    this.isSubmitting = true;
    const { username, password } = this.loginForm.value;
    const totpCode = '';

    this.authService.login({ username, password }, totpCode).subscribe({
      next: (res) => {
        // OPTİMİZE EDİLMİŞ MANTIK
        // Eğer buraya ulaştıysak, backend 200 OK döndü.
        // Backend'in mantığına göre, 2FA aktif olsaydı 418 dönmeliydi.
        // Dolayısıyla 200 OK dönmesi, 2FA'nın aktif OLMADIĞI anlamına gelir.

        this.snackBar.open('Giriş başarılı! İki faktörlü doğrulamayı şimdi aktif edin.', 'Kapat', { duration: 5000 });
        this.router.navigate(['/totp-verify'], { state: { setupFlow: true } });
        this.isSubmitting = false;
      },
      error: (err: any) => { // ⭐ Düzeltme: err tipini 'any' olarak değiştiriyoruz çünkü custom obje olabilir
        this.isSubmitting = false;

        // ⭐ KRİTİK DÜZELTME: Hata objesinin 'type' özelliğini kontrol et ⭐
        if (err && err.type === 'TOTP_REQUIRED') {
          this.snackBar.open('İki faktörlü doğrulama gerekli. Lütfen kodu girin.', 'Kapat', { duration: 3000 });

          this.router.navigate(['/totp-verify'], {
            state: {
              username: username,
              password: password,
              detail: err.detail || 'Two-factor authentication required.'
            }
          });
          console.log('TOTP doğrulama sayfasına yönlendiriliyor...');
        } else {
          // Diğer türdeki HTTP hataları (örneğin 401 Unauthorized gibi) veya bilinmeyen hatalar için
          const errorMessage = (err instanceof HttpErrorResponse) ? (err.error?.detail || err.message) : (err.detail || err.message || 'Bilinmeyen bir giriş hatası oluştu.');
          this.snackBar.open('Giriş hatası: ' + errorMessage, 'Kapat', { duration: 3000 });
          console.error('Giriş başarısız:', err);
        }
      }
    });
  }
}
