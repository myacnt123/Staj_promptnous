// src/app/pages/dashboard/dashboard.component.ts (Prompts bileşeni olarak adlandırılmış)

import { Component, OnInit, OnDestroy } from '@angular/core';
import { Prompt } from '../../models/prompt-model';
import { PromptService} from '../../services/prompt';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Subscription, forkJoin } from 'rxjs'; // forkJoin import edildi
import { PageEvent } from '@angular/material/paginator'; // PageEvent import edildi

@Component({
  selector: 'app-prompts',
  templateUrl: './prompts.html', // prompts.html'i kullanıyor
  standalone: false,
  styleUrls: ['./prompts.css']
})
export class Prompts implements OnInit, OnDestroy { // Component adı Prompts olarak kaldı
  mostLikedPrompts: Prompt[] = [];
  isLoading = true; // Başlangıçta yükleniyor olarak ayarla
  private subscriptions: Subscription[] = []; // Abonelikleri yönetmek için

  // Sayfalama değişkenleri
  totalPrompts = 0;
  pageSize = 12;
  pageIndex = 0;

  constructor(
    private promptService: PromptService,
    private snackBar: MatSnackBar,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadMostLikedPrompts();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe()); // Tüm abonelikleri iptal et
  }

  loadMostLikedPrompts(): void {
    this.isLoading = true;
    const skip = this.pageIndex * this.pageSize;

    const mostLikedSub = forkJoin({
      prompts: this.promptService.getMostLikedPromptsPaginated(skip, this.pageSize),
      totalCount: this.promptService.getMostLikedPromptsTotalCount()
    }).subscribe({
      next: (results) => {
        this.mostLikedPrompts = results.prompts || [];
        this.totalPrompts = results.totalCount || 0;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('En çok beğenilen promptlar yüklenirken hata oluştu:', err);
        this.snackBar.open('Promptlar yüklenemedi. Lütfen daha sonra tekrar deneyin.', 'Kapat', { duration: 3000 });
        this.isLoading = false;
      }
    });
    this.subscriptions.push(mostLikedSub);
  }

  // Sayfalama değiştiğinde çağrılır
  onPageChange(event: PageEvent): void {
    this.pageSize = event.pageSize; // pageSizeOptions olmadığı için bu satırın etkisi olmaz
    this.pageIndex = event.pageIndex;
    this.loadMostLikedPrompts();
  }

  goToPromptDetail(promptId: number): void {
    this.router.navigate(['/prompt-detail/', promptId]);
  }
}
