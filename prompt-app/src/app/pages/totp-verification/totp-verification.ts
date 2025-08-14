import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { Router, ActivatedRoute } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import QRious from 'qrious'; //

@Component({
  selector: 'app-totp-verification',
  standalone: false,
  templateUrl: './totp-verification.html',
  styleUrls: ['./totp-verification.css']
})
export class TotpVerification implements OnInit {
  totpForm!: FormGroup;
  username: string = '';
  password: string = '';
  errorMessage: string = '';

  isTotpActive: boolean = false;
  // qrCodeUri: string | null = null; // ⭐ Doğrudan HTML'e bağlanmadığı için bu değişkeni kaldırdık
  totpSecret: string | null = null;
  showTotpSetupSection: boolean = false;
  isTotpVerifying: boolean = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private router: Router,
    private activatedRoute: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.totpForm = this.fb.group({
      totp_code: ['', [Validators.required, Validators.pattern(/^\d{6}$/)]]
    });

    const state = history.state;
    if (state && (state.username && state.password || state.setupFlow)) {
      if (state.username && state.password) { // 418 hatası sonrası giriş akışı
        this.username = state.username;
        this.password = state.password;
        this.errorMessage = state.detail || '';
        this.showTotpSetupSection = false;
      } else if (state.setupFlow) { // Login sonrası TOTP kurulum akışı
        this.snackBar.open('Lütfen iki faktörlü doğrulamayı aktif edin.', 'Kapat', { duration: 5000 });
        this.checkTotpStatus();
      }
    } else {
      this.checkTotpStatus();
    }
  }

  checkTotpStatus(): void {
    this.authService.isTotpActive().subscribe({
      next: (isActive) => {
        this.isTotpActive = isActive;
        if (!isActive) {
          this.showTotpSetupSection = true;
          this.initiateTotpSetup();
        } else {
          this.showTotpSetupSection = false;
        }
      },
      error: (err) => {
        console.error('TOTP durumu kontrol edilirken hata oluştu:', err);
        this.isTotpActive = false;
        this.snackBar.open('TOTP durumu kontrol edilirken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  onSubmitLoginTotp(): void {
    if (this.totpForm.valid) {
      this.isTotpVerifying = true;
      const totpCode = this.totpForm.value.totp_code;

      this.authService.login({ username: this.username, password: this.password }, totpCode).subscribe({
        next: (res) => {
          this.snackBar.open('Giriş başarılı!', 'Kapat', { duration: 3000 });
          this.router.navigate(['/dashboard']);
        },
        error: (err) => {
          this.errorMessage = err.error?.detail || err.message || 'TOTP doğrulama başarısız.';
          this.snackBar.open(this.errorMessage, 'Kapat', { duration: 3000 });
          this.totpForm.controls['totp_code'].reset();
          this.isTotpVerifying = false;
        }
      });
    } else {
      this.totpForm.markAllAsTouched();
      this.snackBar.open('Lütfen TOTP kodunu doğru formatta girin.', 'Kapat', { duration: 3000 });
    }
  }

  // TOTP kurulumunu başlatır ve secret anahtarını ve QR URI'sini alır
  initiateTotpSetup(): void {
    // this.qrCodeUri = null; // ⭐ Kaldırıldı
    this.totpSecret = null;
    this.totpForm.reset();
    this.isTotpVerifying = false;

    this.authService.setupTotp().subscribe({
      next: (response) => {
        if (response && response.secret && response.qr_uri) {
          this.totpSecret = response.secret;
          // ⭐ QR kodu oluşturma işini generateQrCode metoduna devrettik
          this.generateQrCode(response.qr_uri);
          this.showTotpSetupSection = true;
          this.snackBar.open('TOTP kurulumu başlatıldı. Lütfen QR kodu veya manuel anahtarla uygulamanızı bağlayın.', 'Kapat', { duration: 5000 });
        } else {
          this.snackBar.open('TOTP kurulumu başlatılamadı veya anahtar/QR kodu alınamadı.', 'Kapat', { duration: 3000 });
        }
      },
      error: (err) => {
        console.error('TOTP kurulumu başlatılırken hata oluştu:', err);
        this.snackBar.open('TOTP kurulumu başlatılırken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  // ⭐ Yeni: QR Kodunu Canvas üzerine çizen metot ⭐
  generateQrCode(qrData: string): void {
    // Canvas elementinin DOM'da var olduğundan emin olmak için setTimeout kullanıyoruz.
    // Angular, *ngIf ile bir elementi render ettiğinde hemen DOM'da olmayabilir.
    setTimeout(() => {
      const canvas = document.getElementById('qrCanvas') as HTMLCanvasElement;
      if (canvas) {
        // eslint-disable-next-line no-new
        new QRious({
          element: canvas,
          value: qrData,
          size: 200, // QR kodunun boyutu
          padding: 10,
          background: 'white',
          foreground: 'black',
        });
      } else {
        console.error('QR kod canvas elementi bulunamadı!');
        this.snackBar.open('QR kodu oluşturulamadı (Canvas elementi bulunamadı).', 'Kapat', { duration: 3000 });
      }
    }, 0); // DOM'un güncellenmesini bekle
  }

  verifyTotpSetupFromProfile(): void {
    if (this.totpForm.invalid) {
      this.totpForm.markAllAsTouched();
      this.snackBar.open('Lütfen geçerli bir TOTP kodu girin.', 'Kapat', { duration: 3000 });
      return;
    }

    this.isTotpVerifying = true;
    const totpCode = this.totpForm.value.totp_code;

    if (this.totpSecret) {
      this.authService.verifyTotpSetup(totpCode, this.totpSecret).subscribe({
        next: () => {
          this.snackBar.open('TOTP başarıyla aktif edildi!', 'Kapat', { duration: 3000 });
          this.totpSecret = null;
          // this.qrCodeUri = null; // ⭐ Kaldırıldı
          this.showTotpSetupSection = false;
          this.isTotpActive = true;
          this.isTotpVerifying = false;
        },
        error: (err) => {
          console.error('TOTP doğrulama hatası:', err);
          const errorMessage = err.error?.detail || 'TOTP doğrulama başarısız. Lütfen kodunuzu ve anahtarınızı kontrol edin.';
          this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
          this.isTotpVerifying = false;
          this.totpForm.controls['totp_code'].reset();
        }
      });
    } else {
      this.snackBar.open('TOTP anahtarı bulunamadı. Lütfen kurulumu tekrar başlatın.', 'Kapat', { duration: 3000 });
      this.isTotpVerifying = false;
    }
  }

  deactivateTotp(): void {
    if (confirm('İki faktörlü doğrulamayı devre dışı bırakmak istediğinizden emin misiniz?')) {
      this.authService.deactivateTotp().subscribe({
        next: () => {
          this.snackBar.open('İki faktörlü doğrulama devre dışı bırakıldı.', 'Kapat', { duration: 3000 });
          this.isTotpActive = false;
          this.totpSecret = null;
          // this.qrCodeUri = null; // ⭐ Kaldırıldı
          this.showTotpSetupSection = false;
        },
        error: (err) => {
          console.error('TOTP devre dışı bırakılırken hata oluştu:', err);
          const errorMessage = err.error?.detail || 'TOTP devre dışı bırakma başarısız.';
          this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
        }
      });
    }
  }

  cancelTotpSetup(): void {
    this.showTotpSetupSection = false;
    this.totpSecret = null;
    // this.qrCodeUri = null; // ⭐ Kaldırıldı
    this.totpForm.reset();
  }

  goBackToLogin(): void {
    this.router.navigate(['/login']);
  }

  copySecretToClipboard(): void {
    if (this.totpSecret) {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(this.totpSecret)
          .then(() => {
            this.snackBar.open('Anahtar panoya kopyalandı!', 'Kapat', { duration: 2000 });
          })
          .catch(err => {
            console.error('Panoya kopyalama başarısız oldu (navigator.clipboard):', err);
            this.fallbackCopyToClipboard(this.totpSecret!);
          });
      } else {
        this.fallbackCopyToClipboard(this.totpSecret!);
      }
    } else {
      this.snackBar.open('Kopyalanacak bir anahtar yok.', 'Kapat', { duration: 2000 });
    }
  }

  private fallbackCopyToClipboard(text: string): void {
    const el = document.createElement('textarea');
    el.value = text;
    el.setAttribute('readonly', '');
    el.style.position = 'absolute';
    el.style.left = '-9999px';
    document.body.appendChild(el);
    el.select();
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        this.snackBar.open('Anahtar panoya kopyalandı! (Fallback)', 'Kapat', { duration: 2000 });
      } else {
        this.snackBar.open('Anahtar panoya kopyalanamadı.', 'Kapat', { duration: 2000 });
      }
    } catch (err) {
      console.error('Panoya kopyalama başarısız oldu (execCommand):', err);
      this.snackBar.open('Panoya kopyalama desteklenmiyor veya başarısız.', 'Kapat', { duration: 2000 });
    }
    document.body.removeChild(el);
  }
}
