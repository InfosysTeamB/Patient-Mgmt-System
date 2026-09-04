import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-role-selector',
  templateUrl: './role-selector.component.html',
  styleUrls: ['./role-selector.component.css']
})
export class RoleSelectorComponent {
  isLogin = true;
  errorMsg = '';

  loginForm = { email: '', password: '' };
  registerForm = { name: '', email: '', password: '', role: 'patient', entity_id: '' };

  constructor(private apiService: ApiService, private authService: AuthService, private router: Router) {}

  login(): void {
    this.errorMsg = '';
    this.apiService.login(this.loginForm).subscribe({
      next: (user) => {
        this.authService.setUser(user);
        this.router.navigate(['/' + user.role]);
      },
      error: (err) => {
        this.errorMsg = err.error?.error || 'Login failed';
      }
    });
  }

  register(): void {
    this.errorMsg = '';
    this.apiService.registerUser(this.registerForm).subscribe({
      next: (user) => {
        this.authService.setUser(user);
        this.router.navigate(['/' + user.role]);
      },
      error: (err) => {
        this.errorMsg = err.error?.error || 'Registration failed';
      }
    });
  }

  toggleMode(): void {
    this.isLogin = !this.isLogin;
    this.errorMsg = '';
  }
}
