import { Injectable } from '@angular/core';

const STORAGE_KEY = 'medehr_user';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private user: any = null;

  constructor() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        this.user = JSON.parse(raw);
      } catch {
        localStorage.removeItem(STORAGE_KEY);
        this.user = null;
      }
    }
  }

  setUser(user: any): void {
    this.user = user;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  }

  getUser(): any {
    return this.user;
  }

  getRole(): string {
    return this.user?.role || '';
  }

  getEntityId(): string {
    return this.user?.entity_id || '';
  }

  isLoggedIn(): boolean {
    return this.user !== null;
  }

  logout(): void {
    this.user = null;
    localStorage.removeItem(STORAGE_KEY);
  }
}
