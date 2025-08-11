import { Component, OnInit, OnDestroy } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AdminService } from '../../services/admin';
import { AuthService } from '../../services/auth';
import { User } from '../../models/user-model';
import { Prompt } from '../../models/prompt-model';
import { Label } from '../../models/label-model';
import { LabelService} from '../../services/label';
import { FormControl } from '@angular/forms';
import { Subscription, forkJoin } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { PageEvent } from '@angular/material/paginator';

@Component({
  selector: 'app-admin-panel',
  templateUrl: './admin-panel.html',
  standalone: false,
  styleUrls: ['./admin-panel.css']
})
export class AdminPanel implements OnInit, OnDestroy {
  // Kullanıcı Yönetimi
  users: User[] = [];
  userLoading: boolean = false;
  userDisplayedColumns: string[] = ['id', 'username', 'email', 'is_active', 'is_admin', 'actions'];
  userSearchControl = new FormControl('');
  userTotalItems = 0;
  userPageSize = 10;
  userPageIndex = 0;
  private userSearchSubscription: Subscription = new Subscription();

  // Prompt Yönetimi
  prompts: Prompt[] = [];
  promptLoading: boolean = false;
  promptDisplayedColumns: string[] = ['id', 'content', 'author_username', 'is_public', 'actions'];
  promptSearchControl = new FormControl('');
  promptTotalItems = 0;
  promptPageSize = 10;
  promptPageIndex = 0;
  private promptSearchSubscription: Subscription = new Subscription();

  // Label Yönetimi
  labels: Label[] = [];
  labelLoading: boolean = false;
  labelDisplayedColumns: string[] = ['id', 'name', 'actions'];
  newLabelName: string = '';
  editingLabelId: number | null = null;
  editedLabelName: string = '';

  currentAdminUserId: number | null = null;

  constructor(
    private adminService: AdminService,
    private snackBar: MatSnackBar,
    private authService: AuthService,
    private labelService: LabelService,
  ) { }

  ngOnInit(): void {
    this.authService.getMe().subscribe({
      next: (user) => {
        this.currentAdminUserId = user ? user.id : null;
      },
      error: (err) => {
        console.error('Admin panelde mevcut kullanıcı ID\'si alınamadı:', err);
        this.currentAdminUserId = null;
      }
    });

    this.setupUserSearch();
    this.loadUsers();

    this.setupPromptSearch();
    this.loadPrompts();

    this.loadLabels();
  }

  ngOnDestroy(): void {
    this.userSearchSubscription.unsubscribe();
    this.promptSearchSubscription.unsubscribe();
  }

  // --- Kullanıcı Yönetimi Metotları ---
  setupUserSearch(): void {
    this.userSearchSubscription = this.userSearchControl.valueChanges
      .pipe(
        debounceTime(400),
        distinctUntilChanged()
      )
      .subscribe(() => {
        this.userPageIndex = 0;
        this.loadUsers();
      });
  }

  loadUsers(): void {
    this.userLoading = true;
    const searchTerm = this.userSearchControl.value || '';
    const skip = this.userPageIndex * this.userPageSize;

    forkJoin({
      users: this.adminService.getUsersWithAdminStatusPaginated(searchTerm, skip, this.userPageSize),
      totalCount: this.adminService.getUsersCount(searchTerm)
    }).subscribe({
      next: (results) => {
        this.users = results.users;
        this.userTotalItems = results.totalCount;
        this.userLoading = false;
      },
      error: (error) => {
        console.error('Kullanıcılar yüklenirken hata oluştu:', error);
        this.snackBar.open('Kullanıcılar yüklenemedi.', 'Kapat', { duration: 3000 });
        this.userLoading = false;
      }
    });
  }

  onUserPageChange(event: PageEvent): void {
    this.userPageSize = event.pageSize;
    this.userPageIndex = event.pageIndex;
    this.loadUsers();
  }

  toggleAdminStatus(user: User): void {
    if (user.id === this.currentAdminUserId) {
      this.snackBar.open('Kendi adminlik durumunuzu bu panelden değiştiremezsiniz.', 'Kapat', { duration: 3000 });
      return;
    }

    if (!confirm(`${user.username} adlı kullanıcının yönetici yetkilerini ${user.is_admin ? 'kaldırmak' : 'vermek'} istediğinizden emin misiniz?`)) {
      return;
    }

    const action = user.is_admin
      ? this.adminService.removeAdmin(user.id)
      : this.adminService.addAdmin(user.id);

    action.subscribe({
      next: () => {
        this.loadUsers();
        this.snackBar.open(`${user.username} kullanıcısının yönetici yetkileri başarıyla ${user.is_admin ? 'kaldırıldı' : 'verildi'}.`, 'Kapat', { duration: 3000 });
      },
      error: (error) => {
        console.error('Yönetici yetkisi güncellenirken hata oluştu:', error);
        this.snackBar.open('Yönetici yetkisi güncellenirken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  deleteUser(userId: number): void {
    if (userId === this.currentAdminUserId) {
      this.snackBar.open('Kendi hesabınızı bu panelden silemezsiniz.', 'Kapat', { duration: 3000 });
      return;
    }

    if (confirm(`Kullanıcı ID ${userId} olan hesabı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!`)) {
      this.adminService.adminDeleteUser(userId).subscribe({
        next: () => {
          this.loadUsers();
          this.snackBar.open('Kullanıcı başarıyla silindi.', 'Kapat', { duration: 3000 });
        },
        error: (error) => {
          console.error('Kullanıcı silinirken hata oluştu:', error);
          this.snackBar.open('Kullanıcı silinirken bir sorun oluştu.', 'Kapat', { duration: 3000 });
        }
      });
    }
  }

  // --- Prompt Yönetimi Metotları ---
  setupPromptSearch(): void {
    this.promptSearchSubscription = this.promptSearchControl.valueChanges
      .pipe(
        debounceTime(400),
        distinctUntilChanged()
      )
      .subscribe(() => {
        this.promptPageIndex = 0;
        this.loadPrompts();
      });
  }

  loadPrompts(): void {
    this.promptLoading = true;
    const searchTerm = this.promptSearchControl.value || '';
    const skip = this.promptPageIndex * this.promptPageSize;

    forkJoin({
      prompts: this.adminService.getPromptsForAdminPaginated(searchTerm, skip, this.promptPageSize),
      totalCount: this.adminService.getPromptsForAdminTotalCount(searchTerm)
    }).subscribe({
      next: (results) => {
        this.prompts = results.prompts;
        this.promptTotalItems = results.totalCount;
        this.promptLoading = false;
      },
      error: (error) => {
        console.error('Promptlar yüklenirken hata oluştu:', error);
        this.snackBar.open('Promptlar yüklenemedi.', 'Kapat', { duration: 3000 });
        this.promptLoading = false;
      }
    });
  }

  onPromptPageChange(event: PageEvent): void {
    this.promptPageSize = event.pageSize;
    this.promptPageIndex = event.pageIndex;
    this.loadPrompts();
  }

  deletePrompt(prompt: Prompt): void {
    if (!confirm(`'${prompt.content.substring(0, 30)}...' promptunu silmek istediğinizden emin misiniz?`)) {
      return;
    }

    this.adminService.softDeletePrompt(prompt.id).subscribe({
      next: () => {
        this.loadPrompts();
        this.snackBar.open('Prompt başarıyla silindi.', 'Kapat', { duration: 3000 });
      },
      error: (error) => {
        console.error('Prompt silinirken hata oluştu:', error);
        this.snackBar.open('Prompt silinirken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  // --- Label Yönetimi Metotları ---
  loadLabels(): void {
    this.labelLoading = true;
    this.labelService.getLabels().subscribe({
      next: (data: Label[]) => {
        this.labels = data;
        this.labelLoading = false;
      },
      error: (error) => {
        console.error('Etiketler yüklenirken hata oluştu:', error);
        this.snackBar.open('Etiketler yüklenemedi.', 'Kapat', { duration: 3000 });
        this.labelLoading = false;
      }
    });
  }

  deleteLabelByName(labelName: string): void {
    if (!confirm(`'${labelName}' etiketini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!`)) {
      return;
    }

    this.labelService.deleteLabelByName(labelName).subscribe({
      next: () => {
        this.labels = this.labels.filter(l => l.name !== labelName);
        this.snackBar.open('Etiket başarıyla silindi.', 'Kapat', { duration: 3000 });
      },
      error: (error) => {
        console.error('Etiket silinirken hata oluştu:', error);
        this.snackBar.open('Etiket silinirken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  createLabel(): void {
    if (!this.newLabelName || this.newLabelName.trim() === '') {
      this.snackBar.open('Etiket adı boş bırakılamaz.', 'Kapat', { duration: 3000 });
      return;
    }

    this.labelService.createLabel(this.newLabelName).subscribe({
      next: (newLabel) => {
        this.labels.push(newLabel);
        this.newLabelName = '';
        this.snackBar.open(`'${newLabel.name}' etiketi başarıyla eklendi.`, 'Kapat', { duration: 3000 });
      },
      error: (error) => {
        console.error('Etiket eklenirken hata oluştu:', error);
        this.snackBar.open('Etiket eklenirken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  startEdit(label: Label): void {
    this.editingLabelId = label.id;
    this.editedLabelName = label.name;
  }

  saveLabel(label: Label): void {
    if (!this.editedLabelName || this.editedLabelName.trim() === '') {
      this.snackBar.open('Etiket adı boş bırakılamaz.', 'Kapat', { duration: 3000 });
      return;
    }

    this.labelService.updateLabel(label.id, this.editedLabelName).subscribe({
      next: (updatedLabel) => {
        const index = this.labels.findIndex(l => l.id === updatedLabel.id);
        if (index > -1) {
          this.labels[index] = updatedLabel;
        }
        this.editingLabelId = null;
        this.editedLabelName = '';
        this.snackBar.open(`Etiket başarıyla '${updatedLabel.name}' olarak güncellendi.`, 'Kapat', { duration: 3000 });
      },
      error: (error) => {
        console.error('Etiket güncellenirken hata oluştu:', error);
        this.snackBar.open('Etiket güncellenirken bir sorun oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  cancelEdit(): void {
    this.editingLabelId = null;
    this.editedLabelName = '';
  }
}
