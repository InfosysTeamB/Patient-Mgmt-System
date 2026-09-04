import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private user: any = null;

  setUser(user: any): void {
    this.user = user;
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
  }
}
