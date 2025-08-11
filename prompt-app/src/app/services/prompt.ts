import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, forkJoin, of } from 'rxjs';
import { Prompt } from '../models/prompt-model';
import { Comment } from '../models/comment-model';
import { switchMap, map } from 'rxjs/operators';


@Injectable({
  providedIn: 'root'
})
export class PromptService {
  private apiUrl = 'http://10.6.20.185:8000'; // Buraya backend API'nizin temel URL'sini girin

  constructor(private http: HttpClient) {}

  /**
   * Searches, filters, and paginates public prompts based on search term, single label, skip, and limit.
   */
  searchAndFilterPrompts(searchTerm: string, labelName: string | null, skip: number, limit: number): Observable<Prompt[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (searchTerm) {
      params = params.set('search', searchTerm);
    }

    let requestUrl: string;

    if (labelName) {
      requestUrl = `${this.apiUrl}/labels/most-recent-by-label/${labelName}`;
    } else {
      requestUrl = `${this.apiUrl}/prompts/public_likestatus_most_recent/`;
    }

    console.log('Fetching Public Prompts URL:', `${requestUrl}?${params.toString()}`);

    return this.http.get<Prompt[]>(requestUrl, { params });
  }

  /**
   * Gets the total count of public prompts based on search term and a single label.
   */
  getPromptsCount(searchTerm: string, labelName: string | null): Observable<number> {
    let params = new HttpParams();

    if (searchTerm) {
      params = params.set('search', searchTerm);
    }

    let requestUrl: string;
    let countObservable: Observable<number>;

    if (labelName) {
      params = params.set('label_name', labelName);
      requestUrl = `${this.apiUrl}/prompts/getcountslabel/`;
      countObservable = this.http.get<number>(requestUrl, { params });
    } else {
      requestUrl = `${this.apiUrl}/prompts/getcounts/`;
      countObservable = this.http.get<number>(requestUrl, { params });
    }

    console.log('Counting Public Prompts URL:', `${requestUrl}?${params.toString()}`);

    return countObservable.pipe(
      map(response => {
        return response;
      })
    );
  }

  /**
   * Fetches paginated list of current user's own prompts. NO SEARCH.
   */
  getOwnPromptsPaginated(skip: number, limit: number): Observable<Prompt[]> {
    const params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    const requestUrl = `${this.apiUrl}/prompts/tired/`;
    console.log('Fetching Own Prompts URL:', `${requestUrl}?${params.toString()}`);
    return this.http.get<Prompt[]>(requestUrl, { params });
  }

  /**
   * Gets the total count of current user's own prompts. NO SEARCH.
   */
  getOwnPromptsTotalCount(): Observable<number> {
    const requestUrl = `${this.apiUrl}/prompts/getcountsown/`;
    console.log('Counting Own Prompts URL:', requestUrl);
    return this.http.get<number>(requestUrl).pipe(
      map(response => {
        return response;
      })
    );
  }

  /**
   * Fetches paginated list of current user's favorite prompts.
   */
  getFavoritePromptsPaginated(searchTerm: string, skip: number, limit: number): Observable<Prompt[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (searchTerm) {
      params = params.set('search', searchTerm);
    }
    const requestUrl = `${this.apiUrl}/prompts/favorites/`;
    console.log('Fetching Favorite Prompts URL:', `${requestUrl}?${params.toString()}`);
    return this.http.get<Prompt[]>(requestUrl, { params });
  }

  /**
   * Gets the total count of current user's favorite prompts.
   */
  getFavoritePromptsTotalCount(searchTerm: string): Observable<number> {
    let params = new HttpParams();

    if (searchTerm) {
      params = params.set('search', searchTerm);
    }
    const requestUrl = `${this.apiUrl}/prompts/getcountsliked/`;
    console.log('Counting Favorite Prompts URL:', `${requestUrl}?${params.toString()}`);
    return this.http.get<number>(requestUrl, { params }).pipe(
      map(response => {
        return response;
      })
    );
  }

  /**
   * Fetches paginated list of most liked public prompts. NO SEARCH.
   */
  getMostLikedPromptsPaginated(skip: number, limit: number): Observable<Prompt[]> {
    const params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    const requestUrl = `${this.apiUrl}/prompts/mosst-liked/`;
    console.log('Fetching Most Liked Prompts URL:', `${requestUrl}?${params.toString()}`);
    return this.http.get<Prompt[]>(requestUrl, { params });
  }

  /**
   * Gets the total count of all public prompts (used for Most Liked page). NO SEARCH.
   */
  getMostLikedPromptsTotalCount(): Observable<number> {
    const requestUrl = `${this.apiUrl}/prompts/getcounts/`; // Genel prompt sayısını kullanıyoruz
    console.log('Counting Most Liked Prompts URL:', requestUrl);
    return this.http.get<number>(requestUrl).pipe(
      map(response => {
        return response;
      })
    );
  }

  // --- YENİ EKLENEN METOTLAR: Arama Sayfası İçin ---

  /**
   * Fetches paginated and filtered public prompts for the search page.
   * This is a more generalized version of the searchAndFilterPrompts method for the dashboard.
   */
  searchPublicPromptsPaginated(searchTerm: string, skip: number, limit: number): Observable<Prompt[]> {
    let params = new HttpParams()
      .set('skip', skip.toString())
      .set('limit', limit.toString());

    if (searchTerm) {
      params = params.set('search', searchTerm);
    }
    const requestUrl = `${this.apiUrl}/prompts/public_likestatus_most_recent/`; // Backend'in search parametresini desteklediğini varsayıyoruz
    console.log('Fetching Search Results URL:', `${requestUrl}?${params.toString()}`);
    return this.http.get<Prompt[]>(requestUrl, { params });
  }

  /**
   * Gets the total count of all public prompts based on a search term.
   */
  searchPublicPromptsTotalCount(searchTerm: string): Observable<number> {
    let params = new HttpParams();
    if (searchTerm) {
      params = params.set('search', searchTerm);
    }
    const requestUrl = `${this.apiUrl}/prompts/getcounts/`;
    console.log('Counting Search Results URL:', `${requestUrl}?${params.toString()}`);
    return this.http.get<number>(requestUrl, { params }).pipe(
      map(response => {
        return response;
      })
    );
  }

  // --- Other existing methods (unchanged) ---
  getAllPublicPrompts(): Observable<Prompt[]> {
    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/`);
  }

  getPromptById(promptId: number): Observable<Prompt> {
    return this.http.get<Prompt>(`${this.apiUrl}/prompts/${promptId}`);
  }

  updatePrompt(promptId: number, promptData: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/prompts/${promptId}`, promptData);
  }

  deletePrompt(promptId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/prompts/${promptId}`);
  }

  getPromptWithStatusById(promptId: number): Observable<Prompt> {
    return this.http.get<Prompt>(`${this.apiUrl}/prompts/${promptId}/status`);
  }

  getMostLikedPublicPromptsWithStatus(): Observable<Prompt[]> {
    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/mosst-liked/`);
  }

  getAllPublicPromptsWithLikeStatusRecent(): Observable<Prompt[]> {
    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/public_likestatus_most_recent/`);
  }

  getOwnPromptsWithStatus(): Observable<Prompt[]> {
    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/tired/`);
  }

  getFavoritePrompts(): Observable<Prompt[]> {
    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/favorites/`);
  }

  createPrompt(promptData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/prompts/`, promptData);
  }

  likePrompt(promptId: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/prompts/${promptId}/like`, {});
  }

  unlikePrompt(promptId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/prompts/${promptId}/unlike`);
  }

  createComment(promptId: number, content: string): Observable<Comment> {
    return this.http.post<Comment>(`${this.apiUrl}/prompts/${promptId}/comments`, { content });
  }

  getCommentsForPrompt(promptId: number): Observable<Comment[]> {
    return this.http.get<Comment[]>(`${this.apiUrl}/prompts/${promptId}/comments`);
  }

  getCommentById(commentId: number): Observable<Comment> {
    return this.http.get<Comment>(`${this.apiUrl}/comments/${commentId}`);
  }

  updateComment(commentId: number, content: string): Observable<Comment> {
    return this.http.put<Comment>(`${this.apiUrl}/comments/${commentId}`, { content });
  }

  deleteComment(commentId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/comments/${commentId}`);
  }
  searchPrompts(query: string): Observable<Prompt[]> {
    let params = new HttpParams().set('q', query);
    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/search`, { params });
  }
  getMostLikedPrompts(): Observable<Prompt[]> {
    return this.http.get<Prompt[]>(`${this.apiUrl}/prompts/mosst-liked/`);
  }
}
