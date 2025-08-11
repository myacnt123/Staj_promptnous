// src/app/services/label.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Label} from '../models/label-model';

@Injectable({
  providedIn: 'root'
})
export class LabelService {
  private apiUrl = 'http://10.6.20.185:8000'; // Buraya backend API'nizin temel URL'sini girin

  constructor(private http: HttpClient) { }

  /**
   * Yeni bir etiket oluşturur.
   * POST /labels/
   */
  createLabel(name: string): Observable<Label> {
    return this.http.post<Label>(`${this.apiUrl}/labels/`, { name });
  }

  /**
   * Tüm etiketleri okur.
   * GET /labels/
   */
  getLabels(): Observable<Label[]> {
    return this.http.get<Label[]>(`${this.apiUrl}/labels/`);
  }

  /**
   * Belirli bir etiketi adıyla siler.
   * DELETE /labels/{label_name}
   */
  deleteLabelByName(name: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/labels/${encodeURIComponent(name)}`);
  }

  /**
   * Belirli bir etiketi adıyla okur.
   * GET /labels/{label_name}
   */
  getLabelByName(name: string): Observable<Label> {
    return this.http.get<Label>(`${this.apiUrl}/labels/${encodeURIComponent(name)}`);
  }

  /**
   * Bir prompt'a etiket ekler.
   * POST /labels/{prompt_id}/labels/{label_name}
   */
  addLabelToPrompt(promptId: number, labelName: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/labels/${promptId}/labels/${encodeURIComponent(labelName)}`, {});
  }

  /**
   * Bir prompt'tan etiket kaldırır.
   * DELETE /labels/{prompt_id}/labels/{label_name}
   */
  removeLabelFromPrompt(promptId: number, labelName: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/labels/${promptId}/labels/${encodeURIComponent(labelName)}`);
  }

  /**
   * Belirli bir etikete sahip en beğenilen prompt'ları getirir.
   * GET /labels/most-liked-by-label/{label_name}
   */
  getMostLikedPromptsByLabel(labelName: string): Observable<any[]> { // Prompt modeli yerine any[] kullandım, duruma göre Prompt[] yapabilirsiniz
    return this.http.get<any[]>(`${this.apiUrl}/labels/most-liked-by-label/${encodeURIComponent(labelName)}`);
  }

  /**
   * Belirli bir etikete sahip en yeni prompt'ları getirir.
   * GET /labels/most-recent-by-label/{label_name}
   */
  getMostRecentPromptsByLabel(labelName: string): Observable<any[]> { // Prompt modeli yerine any[] kullandım, duruma göre Prompt[] yapabilirsiniz
    return this.http.get<any[]>(`${this.apiUrl}/labels/most-recent-by-label/${encodeURIComponent(labelName)}`);
  }

  /**
   * Belirli bir prompt'a ait etiketleri getirir.
   * GET /labels/{prompt_id}/labels
   */
  getLabelsForPrompt(promptId: number): Observable<Label[]> {
    return this.http.get<Label[]>(`${this.apiUrl}/labels/${promptId}/labels`);
  }
  updateLabel(labelId: number, newName: string): Observable<Label> {
    const updatedLabel = { name: newName };
    return this.http.put<Label>(`${this.apiUrl}/labels/${labelId}`, updatedLabel);
  }
}
