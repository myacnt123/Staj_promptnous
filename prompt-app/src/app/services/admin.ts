import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, forkJoin, of, throwError } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { User } from '../models/user-model';
import { Prompt } from '../models/prompt-model';

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  isCurrentUserAdmin(): Observable<boolean> {
    return this.http.get<boolean>(`${this.apiUrl}/admin/ifadmin/`).pipe(
      catchError(() => of(false))
    );
  }

  getUsersWithAdminStatusPaginated(searchTerm: string, skip: number, limit: number): Observable<User[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (searchTerm) {
      params = params.set('search', searchTerm);
    }

    return forkJoin([
      this.http.get<User[]>(`${this.apiUrl}/admin/`, { params }),
      this.http.get<User[]>(`${this.apiUrl}/admin/list_admins`)
    ]).pipe(
      map(([allUsers, admins]) => {
        const adminIds = new Set(admins.map(admin => admin.id));
        return allUsers.map(user => ({
          ...user,
          is_admin: adminIds.has(user.id)
        }));
      }),
      catchError(() => of([]))
    );
  }

  getUsersCount(searchTerm: string): Observable<number> {
    let params = new HttpParams();
    if (searchTerm) {
      params = params.set('search', searchTerm);
    }
    return this.http.get<number>(`${this.apiUrl}/admin/usercount/`, { params }).pipe(
      catchError(() => of(0))
    );
  }

  addAdmin(userId: number): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/admin/add_admin/${userId}`, {});
  }

  removeAdmin(userId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/remove_admin/${userId}`);
  }

  adminDeleteUser(userId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/admin/${userId}`);
  }

  getPromptsForAdminPaginated(searchTerm: string, skip: number, limit: number): Observable<Prompt[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (searchTerm) {
      params = params.set('search', searchTerm);
    }

    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/`, { params }).pipe(
      catchError(() => of([]))
    );
  }

  getPromptsForAdminTotalCount(searchTerm: string): Observable<number> {
    let params = new HttpParams();
    if (searchTerm) {
      params = params.set('search', searchTerm);
    }

    return this.http.get<number>(`${this.apiUrl}/prompts/getcounts/`, { params }).pipe(
      catchError(() => of(0))
    );
  }

  softDeletePrompt(promptId: number): Observable<any> {
    return this.http.put(`${this.apiUrl}/admin/${promptId}/soft-delete`, {}).pipe(
      catchError(error => throwError(() => new Error('Prompt silinemedi.')))
    );
  }
}
