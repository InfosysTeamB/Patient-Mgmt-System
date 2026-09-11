import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-doctor-profile',
  templateUrl: './doctor-profile.component.html',
  styleUrls: ['./doctor-profile.component.css']
})
export class DoctorProfileComponent implements OnInit {
  doctorProfile: any = null;
  editMode = false;
  loading = true;
  editForm = {
    doctor_id: '',
    doctor_name: '',
    specialization: ''
  };

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService) {}

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile() {
    this.loading = true;
    const entityId = this.authService.getEntityId();
    this.apiService.getDoctors().subscribe({
      next: (data: any[]) => {
        this.doctorProfile = data.find(d => d.doctor_id === entityId) || null;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load profile.');
        this.loading = false;
      }
    });
  }

  startEdit() {
    if (!this.doctorProfile) return;
    this.editForm = {
      doctor_id: this.doctorProfile.doctor_id,
      doctor_name: this.doctorProfile.doctor_name,
      specialization: this.doctorProfile.specialization
    };
    this.editMode = true;
  }

  cancelEdit() {
    this.editMode = false;
  }

  saveEdit() {
    this.apiService.updateDoctor(this.editForm.doctor_id, this.editForm).subscribe({
      next: () => {
        this.editMode = false;
        this.toast.success('Profile updated successfully!');
        this.loadProfile();
      },
      error: (err) => {
        this.toast.error(err.error?.error || 'Failed to update profile.');
      }
    });
  }
}