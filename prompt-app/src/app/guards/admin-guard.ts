// src/app/guards/admin.guard.ts

import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router, UrlTree } from '@angular/router';
import { Observable, of } from 'rxjs';
import { switchMap, take, catchError, map } from 'rxjs/operators'; // map eklendi
import { AuthService} from '../services/auth';
import { AdminService} from '../services/admin';
import { MatSnackBar } from '@angular/material/snack-bar';

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private adminService: AdminService, // Enjekte edildi
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.authService.isLoggedIn$.pipe( // Kullanıcının giriş yapıp yapmadığını kontrol et
      take(1),
      switchMap(isLoggedIn => {
        if (!isLoggedIn) {
          // Kullanıcı giriş yapmamışsa
          this.snackBar.open('Bu sayfaya erişim için giriş yapmalısınız.', 'Kapat', { duration: 5000 });
          return of(this.router.createUrlTree(['/login'])); // Giriş sayfasına yönlendir
        }

        // Kullanıcı giriş yapmışsa, admin yetkisini kontrol et
        return this.adminService.isCurrentUserAdmin().pipe(
          map(isAdmin => {
            if (isAdmin) {
              return true; // Kullanıcı admin ise erişime izin ver
            } else {
              this.snackBar.open('Bu sayfaya erişim izniniz yok. Yönetici olmalısınız.', 'Kapat', { duration: 5000 });
              return this.router.createUrlTree(['/']); // Ana sayfaya yönlendir
            }
          }),
          catchError(error => {
            console.error('Admin yetki kontrolü sırasında hata:', error);
            this.snackBar.open('Yetkilendirme kontrolü sırasında bir hata oluştu.', 'Kapat', { duration: 5000 });
            return of(this.router.createUrlTree(['/']));
          })
        );
      }),
      catchError(error => {
        console.error('AdminGuard genel hata:', error);
        this.snackBar.open('Yetkilendirme kontrolü sırasında bir hata oluştu.', 'Kapat', { duration: 5000 });
        return of(this.router.createUrlTree(['/']));
      })
    );
  }
}
