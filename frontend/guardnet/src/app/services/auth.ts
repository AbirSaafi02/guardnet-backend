import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  private apiUrl = 'http://127.0.0.1:8000/auth';

  constructor(private http: HttpClient, private router: Router) {}

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/login`, { email, password }).pipe(
      tap((response: any) => {
        localStorage.setItem('token', response.access_token);
        localStorage.setItem('nom', response.nom);
        localStorage.setItem('email', response.email);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('nom');
    localStorage.removeItem('email');
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('token');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getNom(): string | null {
    return localStorage.getItem('nom');
  }
}