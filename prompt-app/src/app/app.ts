import { Component, signal } from '@angular/core';
import {NavigationEnd, Router} from '@angular/router';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  standalone: false,
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('prompt-app');

  showSidebar = true;

  constructor(private router: Router) {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        const url = event.urlAfterRedirects;
        // Sidebar gizlenecek sayfalar
        this.showSidebar = !(url === '/login' || url === '/register');
      }
    });
  }
}
