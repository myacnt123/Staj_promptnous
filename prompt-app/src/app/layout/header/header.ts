// src/app/components/header/header.component.ts
import { Component, OnInit, HostListener, ElementRef } from '@angular/core';
import { AuthService } from '../../services/auth';
import { Observable } from 'rxjs';
import { Router } from '@angular/router';

@Component({
  selector: 'app-header',
  templateUrl: './header.html',
  standalone: false,
  styleUrls: ['./header.css']
})
export class Header implements OnInit {
  isLoggedIn$: Observable<boolean>;
  currentUserUsername$: Observable<string | null>;
  isMobileMenuOpen = false;

  // ElementRef ile bu bileşenin kendisini alıyoruz
  constructor(private authService: AuthService, private router: Router, private elementRef: ElementRef) {
    this.isLoggedIn$ = this.authService.isLoggedIn$;
    this.currentUserUsername$ = this.authService.currentUserUsername$;
  }

  ngOnInit(): void {
    if (this.authService.isLoggedIn() && !this.authService.getUsernameFromLocalStorage()) {
      this.authService.getMe().subscribe({
        error: (err) => {
          console.error('Kullanıcı bilgileri çekilemedi:', err);
        }
      });
    }
  }

  goToProfile(): void {
    this.router.navigate(['/profile']);
    this.isMobileMenuOpen = false; // Navigasyondan sonra menüyü kapat
  }

  logout(): void {
    this.authService.logout();
    this.isMobileMenuOpen = false; // Çıkıştan sonra menüyü kapat
  }

  toggleMobileMenu(): void {
    this.isMobileMenuOpen = !this.isMobileMenuOpen;
  }

  reloadAndNavigate(): void {
    this.router.navigate(['/']).then(() => {
      window.location.reload();
    });
  }

  // Sayfadaki tüm tıklamaları dinler
  @HostListener('document:click', ['$event'])
  onClick(event: Event): void {
    // Tıklamanın bu bileşenin içinde olup olmadığını kontrol et
    const isClickedInside = this.elementRef.nativeElement.contains(event.target);

    // Eğer menü açıksa ve tıklama bileşen dışında olduysa, menüyü kapat
    if (this.isMobileMenuOpen && !isClickedInside) {
      this.isMobileMenuOpen = false;
    }
  }
}
