// src/app/pages/prompt-add/prompt-add.ts
import { Component, OnInit, ElementRef, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormControl } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { Observable, of, forkJoin } from 'rxjs';
import { startWith, map, switchMap, catchError } from 'rxjs/operators';

import { PromptService} from '../../services/prompt';
import { AuthService} from '../../services/auth';
import { LabelService} from '../../services/label';
import { Label } from '../../models/label-model';

@Component({
  selector: 'app-prompt-add',
  templateUrl: './prompt-add.html',
  standalone: false,
  styleUrls: ['./prompt-add.css']
})
export class PromptAdd implements OnInit {
  promptForm!: FormGroup;
  isLoading: boolean = false;

  // Etiket yönetimi için yeni değişkenler
  allLabels: Label[] = [];
  selectedLabels: Label[] = [];
  filteredLabels: Observable<Label[]>;

  @ViewChild('labelInput') labelInput!: ElementRef<HTMLInputElement>;

  constructor(
    private fb: FormBuilder,
    private promptService: PromptService,
    private labelService: LabelService,
    private router: Router,
    private snackBar: MatSnackBar,
    private authService: AuthService
  ) {
    this.filteredLabels = of([]); // Başlangıçta boş bir Observable atayın
  }

  ngOnInit(): void {
    this.promptForm = this.fb.group({
      content: ['', [Validators.required, Validators.minLength(5)]],
      is_public: [true],
      newLabel: new FormControl('') // Etiketler için yeni FormControl
    });

    this.loadAllLabels();

    this.filteredLabels = this.promptForm.get('newLabel')!.valueChanges.pipe(
      startWith(''),
      map(value => this._filter(value || ''))
    );
  }

  private loadAllLabels(): void {
    this.labelService.getLabels().subscribe({
      next: (labels) => {
        this.allLabels = labels;
      },
      error: (err) => {
        console.error('Etiketler yüklenirken hata oluştu:', err);
        this.snackBar.open('Etiketler yüklenirken bir hata oluştu.', 'Kapat', { duration: 3000 });
      }
    });
  }

  private _filter(value: string): Label[] {
    const filterValue = value.toLowerCase();
    const existingLabelNames = this.selectedLabels.map(l => l.name.toLowerCase());
    return this.allLabels.filter(label =>
      label.name.toLowerCase().includes(filterValue) && !existingLabelNames.includes(label.name.toLowerCase())
    );
  }

  selectLabel(event: MatAutocompleteSelectedEvent): void {
    const labelName = event.option.value;
    const labelToAdd = this.allLabels.find(l => l.name === labelName);
    if (labelToAdd && !this.selectedLabels.some(l => l.name === labelToAdd.name)) {
      this.selectedLabels.push(labelToAdd);
    }
    this.labelInput.nativeElement.value = '';
    this.promptForm.get('newLabel')!.setValue(null);
  }

  removeLabel(label: Label): void {
    const index = this.selectedLabels.indexOf(label);
    if (index >= 0) {
      this.selectedLabels.splice(index, 1);
    }
  }

  onSubmit(): void {
    if (!this.promptForm.valid) {
      this.promptForm.markAllAsTouched();
      this.snackBar.open('Lütfen formdaki hataları düzeltin.', 'Kapat', { duration: 3000 });
      return;
    }

    this.isLoading = true;
    const promptData = this.promptForm.value;

    this.promptService.createPrompt(promptData).pipe(
      switchMap(response => {
        const promptId = response.id;
        const addLabelCalls = this.selectedLabels.map(label =>
          this.labelService.addLabelToPrompt(promptId, label.name).pipe(
            catchError(err => {
              console.error(`Prompt'a etiket eklenirken hata:`, err);
              return of(null);
            })
          )
        );
        return forkJoin(addLabelCalls.length > 0 ? addLabelCalls : of(null));
      })
    ).subscribe({
      next: () => {
        this.snackBar.open('Prompt başarıyla eklendi!', 'Kapat', { duration: 3000 });
        this.promptForm.reset({ is_public: true });
        this.selectedLabels = []; // Etiket seçimini de sıfırla
        this.isLoading = false;
        this.router.navigate(['/prompts']);
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Prompt eklenirken hata oluştu:', err);

        if (err.status === 401 || err.status === 403) {
          this.snackBar.open('Oturum süresi dolmuş olabilir. Lütfen tekrar giriş yapın.', 'Kapat', { duration: 5000 });
          this.authService.logout();
        } else {
          const detail = err.error?.detail || err.message || 'Bilinmeyen hata';
          this.snackBar.open('Hata oluştu: ' + detail, 'Kapat', { duration: 5000 });
        }
      }
    });
  }
}
