import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { User } from '../models/user-model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8000';

  private _isLoggedIn = new BehaviorSubject<boolean>(this.checkInitialLoginStatus());
  isLoggedIn$: Observable<boolean> = this._isLoggedIn.asObservable();

  private _currentUserUsername = new BehaviorSubject<string | null>(localStorage.getItem('username'));
  currentUserUsername$: Observable<string | null> = this._currentUserUsername.asObservable();

  constructor(private http: HttpClient, private router: Router) { }

  private checkInitialLoginStatus(): boolean {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    return !!token && !!username;
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, userData);
  }

  login(credentials: any, totpCode: string = ''): Observable<any> {
    const body = {
      username: credentials.username,
      password: credentials.password,
      totp_code: totpCode,
    };

    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });

    return this.http.post(`${this.apiUrl}/auth/token1`, body, { headers }).pipe(
      tap((res: any) => {
        if (res && res.access_token) {
          localStorage.setItem('access_token', res.access_token);
          const usernameFromResponse = res.username;
          if (usernameFromResponse) {
            localStorage.setItem('username', usernameFromResponse);
            this._currentUserUsername.next(usernameFromResponse);
          } else {
            localStorage.setItem('username', credentials.username);
            this._currentUserUsername.next(credentials.username);
          }
          this._isLoggedIn.next(true);
        }
      }),
      catchError(error => {
        console.error('Login error:', error);
        if (error instanceof HttpErrorResponse && error.status === 418) {
          return throwError(() => ({
            type: 'TOTP_REQUIRED',
            username: credentials.username,
            password: credentials.password,
            detail: error.error?.detail || 'Two-factor authentication required.'
          }));
        } else {
          this._isLoggedIn.next(false);
          this._currentUserUsername.next(null);
          return throwError(() => error);
        }
      })
    );
  }

  getMe(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/auth/me`).pipe(
      tap(user => {
        if (user && user.username) {
          localStorage.setItem('username', user.username);
          this._currentUserUsername.next(user.username);
          this._isLoggedIn.next(true);
        }
      }),
      catchError(error => {
        console.error('getMe failed:', error);
        this.logout();
        return of(null as any);
      })
    );
  }

  isLoggedIn(): boolean {
    return this._isLoggedIn.getValue();
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    this._isLoggedIn.next(false);
    this._currentUserUsername.next(null);
    this.router.navigate(['/login']);
  }

  getUsernameFromLocalStorage(): string | null {
    return localStorage.getItem('username');
  }

  changePassword(currentPassword: string, newPassword: string): Observable<any> {
    const body = {
      current_password: currentPassword,
      new_password: newPassword
    };
    return this.http.put(`${this.apiUrl}/users/me/password`, body);
  }

  deleteUserWithPassword(userId: number, password: string): Observable<any> {
    const body = {
      current_password: password,
      user_id: userId
    };
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    const options = {
      headers: headers,
      body: body,
    };
    return this.http.request('delete', `${this.apiUrl}/users/${userId}`, options);
  }



  /**
   * Kullanıcının TOTP'sinin aktif olup olmadığını kontrol eder.
   * GET /totp/totp/iftotp
   * @returns Observable<boolean> - TOTP aktifse true, değilse false
   */
  isTotpActive(): Observable<boolean> {
    return this.http.get<boolean>(`${this.apiUrl}/totp/totp/iftotp`);
  }

  /**
   * TOTP kurulumunu başlatır ve QR kodu için otpauth URI'sini ve secret'ı döndürür.
   * GET /totp/totp/setup
   * @returns Observable<{ secret: string, qr_uri: string }> - Gizli anahtarı ve QR kodu URI'sini içeren obje.
   */
  setupTotp(): Observable<{ secret: string, qr_uri: string }> {
    return this.http.get<{ secret: string, qr_uri: string }>(`${this.apiUrl}/totp/totp/setup`);
  }

  /**
   * TOTP kurulumunu doğrular.
   * POST /totp/totp/verify-setup
   * @param totpCode - Kullanıcının girdiği 6 haneli TOTP kodu.
   * @param secret - Setup sırasında alınan secret anahtarı.
   * @returns Observable<any>
   */
  verifyTotpSetup(totpCode: string, secret: string): Observable<any> { // ⭐ secret parametresi eklendi
    const body = { code: totpCode, totp_secret: secret }; // ⭐ body'ye secret eklendi
    return this.http.post(`${this.apiUrl}/totp/totp/verify-setup`, body);
  }

  /**
   * TOTP'yi devre dışı bırakır.
   * DELETE /totp/totp/deactivate
   * @returns Observable<any>
   */
  deactivateTotp(): Observable<any> {
    const options = {
      headers: new HttpHeaders({ 'Content-Type': 'application/json' }),
      body: {}
    };
    return this.http.request('DELETE', `${this.apiUrl}/totp/totp/deactivate`, options);
  }
}
