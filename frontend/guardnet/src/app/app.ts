import { Component, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { Sidebar } from './components/sidebar/sidebar';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Sidebar, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('guardnet');

  constructor(private router: Router) {}

  isLoginPage(): boolean {
    return this.router.url === '/login';
  }
}