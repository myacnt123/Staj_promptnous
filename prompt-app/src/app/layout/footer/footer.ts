// src/app/layout/footer/footer.ts

import { Component } from '@angular/core';

@Component({
  selector: 'app-footer', // Bu selector'ı app.html dosyasında kullanacağız
  templateUrl: './footer.html',
  styleUrls: ['./footer.css'],
  standalone: false // Mevcut proje yapınıza uygun olarak modüler bileşen olarak ayarlıyoruz
})
export class Footer {
  currentYear: number;

  constructor() {
    this.currentYear = new Date().getFullYear();
  }
}
