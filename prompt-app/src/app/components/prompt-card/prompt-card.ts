// src/app/components/card/card.component.ts

import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { Prompt } from '../../models/prompt-model';
import { PromptService} from '../../services/prompt';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AuthService} from '../../services/auth';

@Component({
  selector: 'app-prompt-card',
  templateUrl: './prompt-card.html',
  standalone: false,
  styleUrls: ['./prompt-card.css']
})
export class PromptCard implements OnInit {
  @Input() prompt!: Prompt;
  @Input() showFavoriteIcon: boolean = false; // Bu input artık doğrudan is_liked_by_user ile entegre olacak
  @Input() isFavoritePage: boolean = false; // Favoriler sayfasında mı kullanılıyor? (Sadece `unlike` butonu için)

  // Beğenme ve detaya gitme olaylarını dışarıya iletmek için EventEmitter kullanıyoruz
  @Output() promptUpdated = new EventEmitter<Prompt>(); // Prompt güncellendiğinde dışarıya bildirmek için
  @Output() cardClicked = new EventEmitter<number>();


  constructor(
    private promptService: PromptService,
    private snackBar: MatSnackBar,
    private authService: AuthService // Kullanıcının login olup olmadığını kontrol etmek için
  ) { }

  ngOnInit(): void {
    if (!this.prompt) {
      console.warn('PromptCardComponent: prompt input is undefined.');
    }
  }

  onCardClick(): void {
    this.cardClicked.emit(this.prompt.id);
  }

  // Beğenme/Beğenmekten Vazgeçme İşlemi
  toggleLikeUnlike(event: Event): void {
    event.stopPropagation(); // Kartın tıklanma olayını engeller

    // Kullanıcının giriş yapmış olup olmadığını kontrol et
    if (!this.authService.isLoggedIn()) {
      this.snackBar.open('Beğenmek için giriş yapmalısınız.', 'Kapat', { duration: 3000 });
      return;
    }

    if (this.prompt.is_liked_by_user) {
      // Beğenilmişse, beğenmekten vazgeç (unlike)
      this.promptService.unlikePrompt(this.prompt.id).subscribe({
        next: () => {
          this.prompt.no_of_likes--;
          this.prompt.is_liked_by_user = false;
          this.snackBar.open('Beğenmekten vazgeçildi.', 'Kapat', { duration: 2000 });
          this.promptUpdated.emit(this.prompt); // Değişikliği parent'a bildir
        },
        error: (err) => {
          console.error('Beğenmekten vazgeçme hatası:', err);
          const errorMessage = err.error?.detail || 'Bir hata oluştu.';
          this.snackBar.open(`Beğenmekten vazgeçilemedi: ${errorMessage}`, 'Kapat', { duration: 3000 });
        }
      });
    } else {
      // Beğenilmemişse, beğen (like)
      this.promptService.likePrompt(this.prompt.id).subscribe({
        next: () => {
          this.prompt.no_of_likes++;
          this.prompt.is_liked_by_user = true;
          this.snackBar.open('Beğenildi!', 'Kapat', { duration: 2000 });
          this.promptUpdated.emit(this.prompt); // Değişikliği parent'a bildir
        },
        error: (err) => {
          console.error('Beğenme hatası:', err);
          const errorMessage = err.error?.detail || 'Bir hata oluştu.';
          this.snackBar.open(`Beğenilemedi: ${errorMessage}`, 'Kapat', { duration: 3000 });
        }
      });
    }
  }

  // Bu metot sadece favoriler sayfasında 'çöp kutusu' butonu için kullanılacak
  onDeleteFromFavoritesClick(event: Event): void {
    event.stopPropagation();
    // Direkt unlike işlemini çağırıyoruz, çünkü favorilerden kaldırmak unlike etmek demektir.
    this.promptService.unlikePrompt(this.prompt.id).subscribe({
      next: () => {
        this.prompt.no_of_likes--;
        this.prompt.is_liked_by_user = false; // Favoriden kaldırıldığı için beğenilmemiş sayılır
        this.snackBar.open('Favorilerden kaldırıldı.', 'Kapat', { duration: 2000 });
        this.promptUpdated.emit(this.prompt); // Parent component'e bildir
      },
      error: (err) => {
        console.error('Favorilerden kaldırma hatası:', err);
        const errorMessage = err.error?.detail || 'Bir hata oluştu.';
        this.snackBar.open(`Favorilerden kaldırılamadı: ${errorMessage}`, 'Kapat', { duration: 3000 });
      }
    });
  }
}
