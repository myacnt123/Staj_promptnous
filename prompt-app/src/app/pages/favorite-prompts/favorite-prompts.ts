import { Component, OnInit, OnDestroy } from '@angular/core';
import { PromptService} from '../../services/prompt';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Prompt } from '../../models/prompt-model';
import { catchError, of, Subscription, forkJoin } from 'rxjs';
import { FormControl } from '@angular/forms';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { PageEvent } from '@angular/material/paginator';

@Component({
  selector: 'app-favorite-prompts',
  templateUrl: './favorite-prompts.html',
  standalone: false,
  styleUrls: ['./favorite-prompts.css']
})
export class FavoritePrompts implements OnInit, OnDestroy {
  favoritePrompts: Prompt[] = [];
  isLoading: boolean = true;
  private subscriptions: Subscription[] = [];

  // Sayfalama değişkenleri
  totalPrompts = 0;
  pageSize = 12;
  pageIndex = 0;

  searchControl = new FormControl('');

  constructor(
    private promptService: PromptService,
    private snackBar: MatSnackBar,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadFavoritePrompts();
    this.setupSearch();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  setupSearch(): void {
    const searchSub = this.searchControl.valueChanges
      .pipe(
        debounceTime(400),
        distinctUntilChanged()
      )
      .subscribe(() => {
        this.pageIndex = 0;
        this.loadFavoritePrompts();
      });
    this.subscriptions.push(searchSub);
  }

  loadFavoritePrompts(): void {
    this.isLoading = true;
    const searchTerm = this.searchControl.value || '';
    const skip = this.pageIndex * this.pageSize;

    const favoritePromptsSub = forkJoin({
      prompts: this.promptService.getFavoritePromptsPaginated(searchTerm, skip, this.pageSize),
      totalCount: this.promptService.getFavoritePromptsTotalCount(searchTerm)
    }).pipe(
      catchError(error => {
        console.error('Favori promptlar yüklenirken hata oluştu:', error);
        this.snackBar.open('Favori promptlar yüklenirken bir hata oluştu.', 'Kapat', { duration: 3000 });
        this.isLoading = false;
        return of({ prompts: [], totalCount: 0 }); // Hata durumunda boş veri döndür
      })
    ).subscribe(results => {
      this.favoritePrompts = results.prompts;
      this.totalPrompts = results.totalCount;
      this.isLoading = false;
    });

    this.subscriptions.push(favoritePromptsSub);
  }

  onPageChange(event: PageEvent): void {
    this.pageSize = event.pageSize;
    this.pageIndex = event.pageIndex;
    this.loadFavoritePrompts();
  }

  goToPromptDetail(promptId: number): void {
    this.router.navigate(['/prompt-detail/', promptId]);
  }

  // Bu metot, backend'inizdeki "unlike" endpoint'ini kullanarak favorilerden kaldırma işlevini sağlar.
  toggleFavorite(prompt: Prompt): void {
    this.snackBar.open('Favorilerden kaldırılıyor...', 'Kapat', { duration: 1500 });
    this.promptService.unlikePrompt(prompt.id).subscribe({
      next: () => {
        this.snackBar.open('Favorilerden kaldırıldı.', 'Kapat', { duration: 2000 });
        this.loadFavoritePrompts(); // Listeyi yeniden yükle
      },
      error: (err) => {
        console.error('Favorilerden kaldırma başarısız:', err);
        const errorMessage = err.error?.detail || 'Favorilerden kaldırılırken bir hata oluştu.';
        this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
      }
    });
  }
}
