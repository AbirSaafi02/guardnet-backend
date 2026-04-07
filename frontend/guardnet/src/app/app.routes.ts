import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { Dashboard } from './pages/dashboard/dashboard';
import { Scan } from './pages/scan/scan';
import { Alertes } from './pages/alertes/alertes';
import { Anomalies } from './pages/anomalies/anomalies';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'dashboard', component: Dashboard },
  { path: 'scan', component: Scan },
  { path: 'alertes', component: Alertes },
  { path: 'anomalies', component: Anomalies },
];
