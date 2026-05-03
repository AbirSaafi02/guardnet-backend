import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Auth } from './auth';

@Injectable({
  providedIn: 'root'
})
export class MonitoringService {
  private apiUrl = 'http://127.0.0.1:8000/monitoring';

  constructor(private http: HttpClient, private auth: Auth) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Authorization': `Bearer ${this.auth.getToken()}`
    });
  }

  getSummary(): Observable<any> {
    return this.http.get(`${this.apiUrl}/summary`, {
      headers: this.getHeaders()
    });
  }

  getDevices(): Observable<any> {
    return this.http.get(`${this.apiUrl}/devices`, {
      headers: this.getHeaders()
    });
  }

  getDeviceHistory(deviceId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/device/${deviceId}/history`, {
      headers: this.getHeaders()
    });
  }

  getTrafficHistory(): Observable<any> {
    return this.http.get(`${this.apiUrl}/traffic/history`, {
      headers: this.getHeaders()
    });
  }
}
