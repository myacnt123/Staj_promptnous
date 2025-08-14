// src/app/pages/prompt-detail/prompt-detail.component.ts

import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators, FormControl } from '@angular/forms';
import { Prompt } from '../../models/prompt-model';
import { Comment } from '../../models/comment-model';
import { Label } from '../../models/label-model';
import { PromptService} from '../../services/prompt';
import { AuthService} from '../../services/auth';
import { LabelService} from '../../services/label';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, Subscription, forkJoin, Observable } from 'rxjs';
import { catchError, startWith, map } from 'rxjs/operators';

@Component({
  selector: 'app-prompt-detail',
  templateUrl: './prompt-detail.html',
  standalone: false,
  styleUrls: ['./prompt-detail.css']
})
export class PromptDetail implements OnInit, OnDestroy {
  promptId!: number;
  promptData?: Prompt;
  updateForm!: FormGroup;
  commentForm!: FormGroup;
  editCommentForm!: FormGroup;
  isEditing: boolean = false;
  isOwner: boolean = false;
  currentUserId: number | null = null;

  comments: Comment[] = [];
  isLoadingComments: boolean = false;
  editingCommentId: number | null = null;

  allLabels: Label[] = [];
  filteredLabels: Observable<Label[]>;
  labelControl = new FormControl<string | Label | null>(null);
  isAddingLabel: boolean = false;

  private authSubscription: Subscription = new Subscription();
  private promptSubscription: Subscription = new Subscription();
  private labelSubscription: Subscription = new Subscription();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private promptService: PromptService,
    private authService: AuthService,
    private labelService: LabelService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar
  ) {
    this.commentForm = this.fb.group({
      content: ['', [Validators.required, Validators.maxLength(500)]]
    });
    this.editCommentForm = this.fb.group({
      content: ['', [Validators.required, Validators.maxLength(500)]]
    });

    this.filteredLabels = this.labelControl.valueChanges.pipe(
      startWith(null),
      map(value => {
        if (typeof value === 'string') {
          return value;
        } else if (value && typeof value === 'object' && 'name' in value) {
          return value.name;
        }
        return '';
      }),
      map(name => (name ? this._filterLabels(name) : this.allLabels.slice()))
    );
  }

  ngOnInit(): void {
    this.authSubscription.add(
      this.authService.getMe().subscribe({
        next: (user) => {
          this.currentUserId = user?.id || null;
          console.log('Current User ID:', this.currentUserId);
          this.loadPromptAndComments();
          this.loadAllLabels();
        },
        error: (err) => {
          console.error('Kullanıcı bilgileri çekilemedi:', err);
          this.currentUserId = null;
          this.snackBar.open('Kullanıcı bilgileri yüklenirken hata oluştu.', 'Kapat', { duration: 3000 });
          this.loadPromptAndComments();
          this.loadAllLabels();
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.authSubscription.unsubscribe();
    this.promptSubscription.unsubscribe();
    this.labelSubscription.unsubscribe();
  }

  loadPromptAndComments(): void {
    this.promptId = Number(this.route.snapshot.paramMap.get('id'));

    if (!this.promptId) {
      this.snackBar.open('Geçersiz Prompt ID.', 'Kapat', { duration: 3000 });
      this.router.navigate(['/prompts']);
      return;
    }

    this.isLoadingComments = true;
    this.promptSubscription.add(
      forkJoin({
        prompt: this.promptService.getPromptWithStatusById(this.promptId).pipe(
          catchError((err: any) => {
            console.error('Prompt detayları yüklenemedi:', err);
            this.snackBar.open('Prompt detayları yüklenirken bir hata oluştu.', 'Kapat', { duration: 3000 });
            return of(undefined);
          })
        ),
        comments: this.promptService.getCommentsForPrompt(this.promptId).pipe(
          catchError((err: any) => {
            console.error('Yorumlar yüklenemedi:', err);
            this.snackBar.open('Yorumlar yüklenirken bir hata oluştu.', 'Kapat', { duration: 3000 });
            return of([]);
          })
        ),
        promptLabels: this.labelService.getLabelsForPrompt(this.promptId).pipe(
          catchError((err: any) => {
            console.error('Prompt etiketleri yüklenemedi:', err);
            return of([]);
          })
        )
      }).subscribe({
        next: (results) => {
          this.promptData = results.prompt;
          this.comments = results.comments.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
          this.isLoadingComments = false;

          if (this.promptData) {
            this.promptData.labels = results.promptLabels;

            this.isOwner = (this.currentUserId !== null && this.promptData.user_id === this.currentUserId);
            this.updateForm = this.fb.group({
              content: [this.promptData.content, Validators.required],
              is_public: [this.promptData.is_public, Validators.required]
            });
          } else {
            this.snackBar.open('Prompt bulunamadı.', 'Kapat', { duration: 3000 });
            this.router.navigate(['/prompts']);
          }
        },
        error: () => {
          this.isLoadingComments = false;
        }
      })
    );
  }

  // --- Etiket Yönetimi Metotları ---
  loadAllLabels(): void {
    this.labelSubscription.add(
      this.labelService.getLabels().subscribe({
        next: (labels: Label[]) => {
          this.allLabels = labels;
        },
        error: (err: any) => {
          console.error('Tüm etiketler yüklenirken hata oluştu:', err);
          this.snackBar.open('Tüm etiketler yüklenirken bir hata oluştu.', 'Kapat', { duration: 3000 });
        }
      })
    );
  }

  private _filterLabels(value: string): Label[] {
    const filterValue = value.toLowerCase();
    return this.allLabels.filter(label => label.name.toLowerCase() === filterValue);
  }

  displayLabel(label?: Label | null): string {
    return label ? label.name : '';
  }

  onLabelSelected(event: any): void {
    const selectedLabel: Label = event.option.value;
    if (selectedLabel) {
      this.labelControl.setValue(selectedLabel);
    }
  }

  addLabelToPrompt(): void {
    if (!this.promptData || !this.authService.isLoggedIn() || !this.isOwner) {
      this.snackBar.open('Etiket eklemek için giriş yapmalısınız ve promptun sahibi olmalısınız.', 'Kapat', { duration: 3000 });
      return;
    }

    const currentLabelValue = this.labelControl.value;
    let labelToAdd: Label | undefined;
    let isNewLabel: boolean = false;

    if (typeof currentLabelValue === 'string') {
      const trimmedValue = currentLabelValue.trim();
      if (!trimmedValue) {
        this.snackBar.open('Lütfen bir etiket adı girin.', 'Kapat', { duration: 2000 });
        return;
      }
      labelToAdd = this.allLabels.find(label => label.name.toLowerCase() === trimmedValue.toLowerCase());
      if (!labelToAdd) {
        labelToAdd = { id: 0, name: trimmedValue };
        isNewLabel = true;
      }
    } else if (currentLabelValue && typeof currentLabelValue === 'object' && 'id' in currentLabelValue && 'name' in currentLabelValue) {
      labelToAdd = currentLabelValue as Label;
    } else {
      this.snackBar.open('Geçersiz etiket seçimi.', 'Kapat', { duration: 2000 });
      return;
    }

    if (!labelToAdd) {
      this.snackBar.open('Etiket eklenemedi: Etiket bilgisi eksik.', 'Kapat', { duration: 2000 });
      return;
    }

    if (this.promptData.labels.some(l => (l.id && l.id === labelToAdd!.id) || (l.name.toLowerCase() === labelToAdd!.name.toLowerCase()))) {
      this.snackBar.open('Bu etiket zaten prompta eklenmiş.', 'Kapat', { duration: 2000 });
      this.resetLabelInput();
      return;
    }

    if (isNewLabel) {
      this.labelService.createLabel(labelToAdd.name).subscribe({
        next: (createdLabel: Label) => {
          this.allLabels.push(createdLabel);
          this._addLabelToPromptApi(this.promptData!.id, createdLabel.name, createdLabel);
        },
        error: (err: any) => {
          console.error('Etiket oluşturma hatası:', err);
          const errorMessage = err.error?.detail || 'Etiket oluşturulurken bir hata oluştu.';
          this.snackBar.open(`Etiket oluşturulamadı: ${errorMessage}`, 'Kapat', { duration: 3000 });
        }
      });
    } else if (labelToAdd.name) {
      this._addLabelToPromptApi(this.promptData.id, labelToAdd.name, labelToAdd);
    }
  }

  private _addLabelToPromptApi(promptId: number, labelName: string, addedLabel: Label): void {
    this.labelService.addLabelToPrompt(promptId, labelName).subscribe({
      next: () => {
        if (this.promptData && !this.promptData.labels.some(l => l.id === addedLabel.id)) {
          this.promptData.labels.push(addedLabel);
        }
        this.snackBar.open('Etiket başarıyla eklendi!', 'Kapat', { duration: 2000 });
        this.resetLabelInput();
      },
      error: (err: any) => {
        console.error('Prompta etiket ekleme hatası:', err);
        const errorMessage = err.error?.detail || 'Etiket eklenirken bir hata oluştu.';
        this.snackBar.open(`Etiket eklenemedi: ${errorMessage}`, 'Kapat', { duration: 3000 });
      }
    });
  }

  removeLabelFromPrompt(labelToRemove: Label): void {
    if (!this.promptData || !this.authService.isLoggedIn() || !this.isOwner) {
      this.snackBar.open('Etiket kaldırmak için giriş yapmalısınız ve promptun sahibi olmalısınız.', 'Kapat', { duration: 3000 });
      return;
    }

    if (confirm(`'${labelToRemove.name}' etiketini prompttan kaldırmak istediğinizden emin misiniz?`)) {
      this.labelService.removeLabelFromPrompt(this.promptData.id, labelToRemove.name).subscribe({
        next: () => {
          if (this.promptData) {
            this.promptData.labels = this.promptData.labels.filter(l => l.id !== labelToRemove.id);
          }
          this.snackBar.open('Etiket başarıyla kaldırıldı!', 'Kapat', { duration: 2000 });
        },
        error: (err: any) => {
          console.error('Prompttan etiket kaldırma hatası:', err);
          const errorMessage = err.error?.detail || 'Etiket kaldırılamadı.';
          this.snackBar.open(`Etiket kaldırılamadı: ${errorMessage}`, 'Kapat', { duration: 3000 });
        }
      });
    }
  }

  resetLabelInput(): void {
    this.labelControl.reset();
    this.isAddingLabel = false;
  }

  // --- Yeni eklenen metotlar ---

  copyPromptContent(): void {
    if (this.promptData?.content) {
      navigator.clipboard.writeText(this.promptData.content)
        .then(() => {
          this.snackBar.open('Prompt içeriği panoya kopyalandı!', 'Kapat', { duration: 2000 });
        })
        .catch(err => {
          console.error('Kopyalama başarısız:', err);
          this.snackBar.open('Kopyalama başarısız oldu.', 'Kapat', { duration: 3000 });
        });
    } else {
      this.snackBar.open('Kopyalanacak bir prompt içeriği yok.', 'Kapat', { duration: 2000 });
    }
  }

  sendToAI(aiName: 'chatgpt' | 'gemini' | 'copilot' | 'grok'): void {
    const promptContent = this.promptData?.content;
    if (!promptContent) {
      this.snackBar.open('Gönderilecek bir prompt içeriği yok.', 'Kapat', { duration: 2000 });
      return;
    }

    const encodedPrompt = encodeURIComponent(promptContent);
    let url: string = '';
    let message: string = '';

    switch (aiName) {
      case 'chatgpt':
        url = `https://chat.openai.com/?prompt=${encodedPrompt}`;
        break;
      case 'gemini':
        this.copyPromptContent();
        message = 'Gemini için prompt panoya kopyalandı. Lütfen editörünüzde yapıştırın.';
        break;
      case 'copilot':
        url = `https://github.com/copilot?prompt=${encodedPrompt}`;
        break;
      case 'grok':
        url = `https://grok.com/chat?reasoningMode=none&q=${encodedPrompt}`;
        break;
    }

    if (url) {
      window.open(url, '_blank');
    }

    if (message) {
      this.snackBar.open(message, 'Kapat', { duration: 5000 });
    }
  }

  // --- Mevcut Diğer Metotlar ---
  toggleLikeUnlike(): void {
    if (!this.promptData) {
      return;
    }

    if (!this.authService.isLoggedIn()) {
      this.snackBar.open('Beğenmek için giriş yapmalısınız.', 'Kapat', { duration: 3000 });
      return;
    }

    if (this.promptData.is_liked_by_user) {
      this.promptService.unlikePrompt(this.promptData.id).subscribe({
        next: () => {
          if (this.promptData) {
            this.promptData.no_of_likes--;
            this.promptData.is_liked_by_user = false;
          }
          this.snackBar.open('Beğenmekten vazgeçildi.', 'Kapat', { duration: 2000 });
        },
        error: (err) => {
          console.error('Beğenmekten vazgeçme hatası:', err);
          const errorMessage = err.error?.detail || 'Bir hata oluştu.';
          this.snackBar.open(`Beğenmekten vazgeçilemedi: ${errorMessage}`, 'Kapat', { duration: 3000 });
        }
      });
    } else {
      this.promptService.likePrompt(this.promptData.id).subscribe({
        next: () => {
          if (this.promptData) {
            this.promptData.no_of_likes++;
            this.promptData.is_liked_by_user = true;
          }
          this.snackBar.open('Beğenildi!', 'Kapat', { duration: 2000 });
        },
        error: (err) => {
          console.error('Beğenme hatası:', err);
          const errorMessage = err.error?.detail || 'Bir hata oluştu.';
          this.snackBar.open(`Beğenilemedi: ${errorMessage}`, 'Kapat', { duration: 3000 });
        }
      });
    }
  }

  toggleEditMode(): void {
    this.isEditing = !this.isEditing;
    if (this.isEditing && this.promptData) {
      this.updateForm.patchValue({
        content: this.promptData.content,
        is_public: this.promptData.is_public
      });
    }
  }

  updatePrompt(): void {
    if (this.updateForm.valid && this.promptId) {
      const updatedData = this.updateForm.value;
      this.promptService.updatePrompt(this.promptId, updatedData).subscribe({
        next: (res: any) => {
          this.snackBar.open('Prompt başarıyla güncellendi!', 'Kapat', { duration: 3000 });
          this.promptData = { ...this.promptData!, ...updatedData };
          this.isEditing = false;
        },
        error: (err: any) => {
          console.error('Prompt güncelleme hatası:', err);
          const errorMessage = err.error?.detail || 'Prompt güncelleme başarısız.';
          this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
        }
      });
    } else {
      this.updateForm.markAllAsTouched();
      this.snackBar.open('Lütfen formdaki hataları düzeltin.', 'Kapat', { duration: 3000 });
    }
  }

  deletePrompt(): void {
    if (confirm('Bu promptu silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
      if (this.promptId) {
        this.promptService.deletePrompt(this.promptId).subscribe({
          next: () => {
            this.snackBar.open('Prompt başarıyla silindi!', 'Kapat', { duration: 3000 });
            this.router.navigate(['/prompts']);
          },
          error: (err: any) => {
            console.error('Prompt silme hatası:', err);
            const errorMessage = err.error?.detail || 'Prompt silme başarısız.';
            this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
          }
        });
      }
    }
  }

  postComment(): void {
    if (this.commentForm.valid && this.promptId) {
      const content = this.commentForm.value.content;
      this.promptService.createComment(this.promptId, content).subscribe({
        next: (newComment: Comment) => {
          this.comments.push(newComment);
          this.comments.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
          this.commentForm.reset();
          this.snackBar.open('Yorum başarıyla eklendi!', 'Kapat', { duration: 2000 });
        },
        error: (err: any) => {
          console.error('Yorum ekleme hatası:', err);
          const errorMessage = err.error?.detail || 'Yorum eklenirken bir hata oluştu.';
          this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
        }
      });
    } else {
      this.commentForm.markAllAsTouched();
      this.snackBar.open('Yorum içeriği boş olamaz veya çok uzun.', 'Kapat', { duration: 3000 });
    }
  }

  editComment(comment: Comment): void {
    this.editingCommentId = comment.comment_id;
    this.editCommentForm.patchValue({ content: comment.content });

    const element = document.getElementById(`comment-${comment.comment_id}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  updateComment(): void {
    if (this.editCommentForm.valid && this.editingCommentId !== null) {
      const updatedContent = this.editCommentForm.value.content;
      this.promptService.updateComment(this.editingCommentId, updatedContent).subscribe({
        next: (updatedComment: Comment) => {
          const index = this.comments.findIndex(c => c.comment_id === updatedComment.comment_id);
          if (index > -1) {
            this.comments[index] = updatedComment;
            this.comments.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
          }
          this.cancelEditComment();
          this.snackBar.open('Yorum başarıyla güncellendi!', 'Kapat', { duration: 2000 });
        },
        error: (err: any) => {
          console.error('Yorum güncelleme hatası:', err);
          const errorMessage = err.error?.detail || 'Yorum güncellenirken bir hata oluştu.';
          this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
        }
      });
    } else {
      this.editCommentForm.markAllAsTouched();
      this.snackBar.open('Yorum içeriği boş olamaz veya çok uzun.', 'Kapat', { duration: 3000 });
    }
  }

  cancelEditComment(): void {
    this.editingCommentId = null;
    this.editCommentForm.reset();
  }

  deleteComment(commentId: number): void {
    if (confirm('Bu yorumu silmek istediğinizden emin misiniz?')) {
      this.promptService.deleteComment(commentId).subscribe({
        next: () => {
          this.comments = this.comments.filter(c => c.comment_id !== commentId);
          this.snackBar.open('Yorum başarıyla silindi!', 'Kapat', { duration: 2000 });
        },
        error: (err: any) => {
          console.error('Yorum silme hatası:', err);
          const errorMessage = err.error?.detail || 'Yorum silinirken bir hata oluştu.';
          this.snackBar.open(errorMessage, 'Kapat', { duration: 3000 });
        }
      });
    }
  }

  isCommentOwner(commentUserId: number): boolean {
    return this.currentUserId !== null && commentUserId === this.currentUserId;
  }

  goBack(): void {
    window.history.back();
  }
}
