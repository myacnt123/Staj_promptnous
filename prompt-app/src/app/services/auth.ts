// src/app/services/auth.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { User } from '../models/user-model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://10.6.20.185:8000';

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

  login(credentials: any): Observable<any> {
    const body = new URLSearchParams();
    body.set('username', credentials.username);
    body.set('password', credentials.password);
    body.set('client_id', 'your_client_id');
    body.set('client_secret', 'your_client_secret');
    body.set('grant_type', 'password');

    const headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
    };

    return this.http.post(`${this.apiUrl}/auth/token`, body.toString(), { headers }).pipe(
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
        this._isLoggedIn.next(false);
        this._currentUserUsername.next(null);
        throw error;
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

  /**
   * Kullanıcının hesabını şifre ve ID ile silme metodu.
   * DELETE /users/{user_id} endpoint'ine doğru body formatıyla istek gönderir.
   */
  deleteUserWithPassword(userId: number, password: string): Observable<any> {
    // API'nin beklediği tam request body'yi oluşturuyoruz.
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
}
