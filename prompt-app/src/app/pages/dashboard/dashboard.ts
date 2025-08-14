import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { Prompt } from '../../models/prompt-model';
import { PromptService} from '../../services/prompt';
import { Label } from '../../models/label-model';
import { LabelService} from '../../services/label';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription, forkJoin } from 'rxjs';
import { FormControl } from '@angular/forms';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { PageEvent } from '@angular/material/paginator';

@Component({
  selector: 'app-prompts',
  templateUrl: './dashboard.html',
  standalone: false,
  styleUrls: ['./dashboard.css']
})
export class Dashboard implements OnInit, OnDestroy {
  prompts: Prompt[] = [];
  allLabels: Label[] = [];
  selectedLabel: string | null = null; // Tek bir etiket seçimi için güncellendi
  isLoading: boolean = true;

  // Sayfalama değişkenleri
  totalPrompts = 0; // Toplam prompt sayısı API'dan gelecek
  pageSize = 12; // Bir sayfada gösterilecek prompt sayısı
  pageIndex = 0; // Mevcut sayfa indexi (0'dan başlar)

  searchControl = new FormControl('');
  private subscriptions: Subscription[] = [];

  constructor(
    private promptService: PromptService,
    private labelService: LabelService,
    private router: Router,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit(): void {
    this.loadLabelsAndSetupFiltering();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  loadLabelsAndSetupFiltering(): void {
    this.isLoading = true;
    const labelsSub = this.labelService.getLabels().subscribe({
      next: (labels: Label[]) => {
        this.allLabels = labels;
        this.filterPrompts(); // Etiketler yüklendiğinde ilk promptları getir
        this.setupSearch();
      },
      error: (err) => {
        console.error('Etiketler yüklenirken hata oluştu:', err);
        this.snackBar.open('Etiketler yüklenirken bir hata oluştu.', 'Kapat', { duration: 3000 });
        this.filterPrompts(); // Hata olsa bile promptları getirmeye çalış
      }
    });
    this.subscriptions.push(labelsSub);
  }

  setupSearch(): void {
    const searchSub = this.searchControl.valueChanges
      .pipe(
        debounceTime(400),
        distinctUntilChanged()
      )
      .subscribe(() => {
        this.pageIndex = 0; // Arama yapıldığında sayfayı sıfırla
        this.filterPrompts();
      });
    this.subscriptions.push(searchSub);
  }

  filterPrompts(): void {
    this.isLoading = true;
    const searchTerm = this.searchControl.value || '';
    const skip = this.pageIndex * this.pageSize;

    // Hem promptları hem de toplam sayıyı aynı anda çekmek için forkJoin kullanıyoruz.
    const promptsAndCountSub = forkJoin({
      // searchAndFilterPrompts metoduna tek etiket gönderildi
      prompts: this.promptService.searchAndFilterPrompts(searchTerm, this.selectedLabel, skip, this.pageSize),
      // getPromptsCount metoduna tek etiket gönderildi
      totalCount: this.promptService.getPromptsCount(searchTerm, this.selectedLabel)
    }).subscribe({
      next: (results) => {
        this.prompts = results.prompts || []; // API'dan dönen direkt diziyi atar
        this.totalPrompts = results.totalCount || 0; // Toplam prompt sayısını günceller
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Promptlar yüklenirken veya filtrelenirken hata oluştu:', err);
        this.isLoading = false;
        this.prompts = [];
        this.totalPrompts = 0;
        this.snackBar.open('Promptları filtrelerken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
    this.subscriptions.push(promptsAndCountSub);
  }

  onLabelChipClick(labelName: string): void {
    // Eğer tıklanan etiket zaten seçiliyse, seçimi kaldır (null yap)
    if (this.selectedLabel === labelName) {
      this.selectedLabel = null;
    } else {
      // Değilse, yeni etiketi seç
      this.selectedLabel = labelName;
    }
    this.pageIndex = 0; // Etiket filtresi değiştiğinde sayfayı sıfırla
    this.filterPrompts();
  }

  // Sayfalama değiştiğinde çağrılır
  onPageChange(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.filterPrompts();
  }

  goToPromptDetail(promptId: number): void {
    this.router.navigate(['/prompt-detail', promptId]);
  }
}
