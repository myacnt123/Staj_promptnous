// src/app/pages/search/search.component.ts

import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { PromptService } from '../../services/prompt';
import { Prompt } from '../../models/prompt-model';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-search',
  templateUrl: './search.html',
  standalone: false,
  styleUrls: ['./search.css']
})
export class Search implements OnInit, OnDestroy {
  searchControl = new FormControl('');
  prompts: Prompt[] = []; // Gösterilecek promptlar
  allPrompts: Prompt[] = []; // Tüm promptların tutulacağı ana liste
  isLoading = false;
  private searchSubscription: Subscription = new Subscription();

  constructor(
    private promptService: PromptService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Sayfa açıldığında tüm promptları arka planda çek
    this.loadAllPrompts();

    // Arama kutusundaki değişiklikleri dinle
    this.searchSubscription = this.searchControl.valueChanges
      .pipe(
        debounceTime(500),
        distinctUntilChanged()
      )
      .subscribe(query => {
        this.filterPrompts(query);
      });
  }

  ngOnDestroy(): void {
    this.searchSubscription.unsubscribe();
  }

  loadAllPrompts(): void {
    this.isLoading = true;
    this.promptService.getAllPublicPromptsWithLikeStatusRecent().subscribe({
      next: (allPrompts) => {
        this.allPrompts = allPrompts;
        // BAŞLANGIÇTA 'prompts' LİSTESİNİ BOŞ BIRAKIYORUZ.
        // this.prompts = allPrompts; satırı kaldırıldı.
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Promptlar yüklenemedi:', err);
        this.snackBar.open('Promptlar yüklenirken bir hata oluştu.', 'Kapat', { duration: 3000 });
        this.isLoading = false;
      }
    });
  }

  filterPrompts(query: string | null): void {
    if (!query || query.trim() === '') {
      this.prompts = []; // Sorgu boşsa, gösterilecek listeyi boşalt
      return;
    }

    const lowerCaseQuery = query.toLowerCase().trim();

    this.prompts = this.allPrompts.filter(prompt =>
      (prompt.content && prompt.content.toLowerCase().includes(lowerCaseQuery)) ||
      (prompt.author_username && prompt.author_username.toLowerCase().includes(lowerCaseQuery)) ||
      (prompt.labels && prompt.labels.some(label => label.name.toLowerCase().includes(lowerCaseQuery)))
    );
  }

  goToPromptDetail(promptId: number): void {
    this.router.navigate(['/prompt-detail/', promptId]);
  }
}
