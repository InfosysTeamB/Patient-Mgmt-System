import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-role-selector',
  templateUrl: './role-selector.component.html',
  styleUrls: ['./role-selector.component.css']
})
export class RoleSelectorComponent implements OnInit {
  isLogin = true;
  errorMsg = '';
  infoMsg = '';

  loginForm = { email: '', password: '' };
  registerForm = {
    name: '',
    email: '',
    password: '',
    role: 'patient',
    entity_id: '',
    contact_number: '',
    date_of_birth: '',
    gender: '',
    blood_group: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_number: ''
  };

  constructor(private apiService: ApiService, private authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    if (this.authService.isLoggedIn()) {
      this.router.navigate(['/' + this.authService.getRole()]);
    }
  }

  private describeError(err: any, fallback: string): string {
    if (err.status === 0) {
      return 'Cannot reach the server. Make sure the backend is running (python manage.py runserver) and try again.';
    }
    return err.error?.error || fallback;
  }

  login(): void {
    this.errorMsg = '';
    this.apiService.login(this.loginForm).subscribe({
      next: (user) => {
        this.authService.setUser(user);
        this.router.navigate(['/' + user.role]);
      },
      error: (err) => {
        this.errorMsg = this.describeError(err, 'Login failed');
      }
    });
  }

  register(): void {
    this.errorMsg = '';
    this.apiService.registerUser(this.registerForm).subscribe({
      next: (user) => {
        if (user && user.pending_approval) {
          this.infoMsg = user.message || 'Your registration has been submitted for admin approval.';
          this.isLogin = true;
          this.resetRegisterForm();
          return;
        }
        this.authService.setUser(user);
        this.router.navigate(['/' + user.role]);
      },
      error: (err) => {
        this.errorMsg = this.describeError(err, 'Registration failed');
      }
    });
  }

  private resetRegisterForm(): void {
    this.registerForm = {
      name: '',
      email: '',
      password: '',
      role: 'patient',
      entity_id: '',
      contact_number: '',
      date_of_birth: '',
      gender: '',
      blood_group: '',
      address: '',
      emergency_contact_name: '',
      emergency_contact_number: ''
    };
  }

  toggleMode(): void {
    this.isLogin = !this.isLogin;
    this.errorMsg = '';
    this.infoMsg = '';
  }
}
