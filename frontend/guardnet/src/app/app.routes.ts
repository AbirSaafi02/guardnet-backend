import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { Dashboard } from './pages/dashboard/dashboard';
import { Scan } from './pages/scan/scan';
import { Alertes } from './pages/alertes/alertes';
import { Anomalies } from './pages/anomalies/anomalies';
import { Profil } from './pages/profil/profil';
import { AuthGuard } from './guards/auth-guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'dashboard', component: Dashboard, canActivate: [AuthGuard] },
  { path: 'scan', component: Scan, canActivate: [AuthGuard] },
  { path: 'alertes', component: Alertes, canActivate: [AuthGuard] },
  { path: 'anomalies', component: Anomalies, canActivate: [AuthGuard] },
  { path: 'profil', component: Profil, canActivate: [AuthGuard] },
];