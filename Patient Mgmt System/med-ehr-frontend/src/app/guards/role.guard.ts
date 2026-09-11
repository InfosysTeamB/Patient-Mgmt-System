import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree, ActivatedRouteSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot): boolean | UrlTree {
    if (!this.authService.isLoggedIn()) {
      return this.router.parseUrl('/');
    }

    const allowedRoles: string[] = route.data['roles'] || [];
    const userRole = this.authService.getRole();

    if (allowedRoles.length === 0 || allowedRoles.includes(userRole)) {
      return true;
    }

    return this.router.parseUrl('/' + userRole);
  }
}
