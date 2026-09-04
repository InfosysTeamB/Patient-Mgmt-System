import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-doctor-profile',
  templateUrl: './doctor-profile.component.html',
  styleUrls: ['./doctor-profile.component.css']
})
export class DoctorProfileComponent implements OnInit {
  doctorProfile: any = null;
  editMode = false;
  editForm = {
    doctor_id: '',
    doctor_name: '',
    specialization: ''
  };
  msg = '';

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile() {
    const entityId = this.authService.getEntityId();
    this.apiService.getDoctors().subscribe((data: any[]) => {
      this.doctorProfile = data.find(d => d.doctor_id === entityId) || null;
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
    this.msg = '';
  }

  cancelEdit() {
    this.editMode = false;
    this.msg = '';
  }

  saveEdit() {
    this.apiService.updateDoctor(this.editForm.doctor_id, this.editForm).subscribe({
      next: () => {
        this.editMode = false;
        this.msg = 'Profile updated successfully!';
        this.loadProfile();
      },
      error: (err) => {
        this.msg = err.error?.error || 'Failed to update profile.';
      }
    });
  }
}
