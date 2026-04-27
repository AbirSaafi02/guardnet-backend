import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Auth } from '../../services/auth';

@Component({
  selector: 'app-profil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './profil.html',
  styleUrl: './profil.css'
})
export class Profil {
  nom: string = localStorage.getItem('nom') || '';
  email: string = localStorage.getItem('email') || '';
  
  ancienPassword: string = '';
  nouveauPassword: string = '';
  confirmPassword: string = '';
  
  successMessage: string = '';
  errorMessage: string = '';

  constructor(
    private http: HttpClient, 
    private authService: Auth,
    private cdr: ChangeDetectorRef
  ) {}

  changerMotDePasse(): void {
    this.successMessage = '';
    this.errorMessage = '';

    if (this.nouveauPassword !== this.confirmPassword) {
      this.errorMessage = 'Les mots de passe ne correspondent pas !';
      this.cdr.detectChanges();
      return;
    }

    if (this.nouveauPassword.trim().length < 6) {
      this.errorMessage = 'Le mot de passe doit contenir au moins 6 caractères !';
      this.cdr.detectChanges();
      return;
    }

    const token = this.authService.getToken();
    const headers = new HttpHeaders({ Authorization: `Bearer ${token}` });

    this.http.put('http://127.0.0.1:8000/auth/change-password', {
      ancien_password: this.ancienPassword,
      nouveau_password: this.nouveauPassword
    }, { headers }).subscribe({
      next: () => {
        this.successMessage = 'Mot de passe changé avec succès !';
        this.ancienPassword = '';
        this.nouveauPassword = '';
        this.confirmPassword = '';
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Ancien mot de passe incorrect !';
        this.cdr.detectChanges();
      }
    });
  }
}