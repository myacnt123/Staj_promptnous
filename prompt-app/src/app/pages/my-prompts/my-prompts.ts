// src/app/pages/my-prompts/my-prompts.component.ts

import { Component, OnInit, OnDestroy } from '@angular/core';
import { Prompt } from '../../models/prompt-model';
import { PromptService} from '../../services/prompt';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription, forkJoin } from 'rxjs';
import { Router } from '@angular/router';
import { PageEvent } from '@angular/material/paginator';

@Component({
  selector: 'app-my-prompts',
  templateUrl: './my-prompts.html',
  standalone: false,
  styleUrls: ['./my-prompts.css']
})
export class MyPrompts implements OnInit, OnDestroy {
  myPrompts: Prompt[] = [];
  isLoading: boolean = true;
  private subscriptions: Subscription[] = [];

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
    this.loadMyPrompts();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  loadMyPrompts(): void {
    this.isLoading = true;
    const skip = this.pageIndex * this.pageSize;

    const myPromptsSub = forkJoin({
      prompts: this.promptService.getOwnPromptsPaginated(skip, this.pageSize),
      totalCount: this.promptService.getOwnPromptsTotalCount()
    }).subscribe({
      next: (results) => {
        this.myPrompts = results.prompts || [];
        this.totalPrompts = results.totalCount || 0;
        this.isLoading = false;
      },
      error: (err: any) => {
        console.error('Kendi promptlarınız yüklenirken hata oluştu:', err);
        this.isLoading = false;
        this.myPrompts = [];
        this.totalPrompts = 0;
        this.snackBar.open('Promptlarınızı yüklerken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
    this.subscriptions.push(myPromptsSub);
  }

  onPageChange(event: PageEvent): void {
    this.pageSize = event.pageSize;
    this.pageIndex = event.pageIndex;
    this.loadMyPrompts();
  }

  goToPromptDetail(promptId: number): void {
    this.router.navigate(['/prompt-detail', promptId]);
  }
}
