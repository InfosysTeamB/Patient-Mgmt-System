import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-patient-profile',
  templateUrl: './patient-profile.component.html',
  styleUrls: ['./patient-profile.component.css']
})
export class PatientProfileComponent implements OnInit {
  patientProfile: any = null;
  editMode = false;
  loading = true;
  editForm = {
    patient_id: '',
    full_name: '',
    contact_number: '',
    email_address: '',
    date_of_birth: '',
    gender: '',
    blood_group: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_number: ''
  };

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService) {}

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile() {
    this.loading = true;
    const entityId = this.authService.getEntityId();
    this.apiService.getPatients().subscribe({
      next: (data: any[]) => {
        this.patientProfile = data.find(p => p.patient_id === entityId) || null;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load profile.');
        this.loading = false;
      }
    });
  }

  startEdit() {
    if (!this.patientProfile) return;
    this.editForm = {
      patient_id: this.patientProfile.patient_id,
      full_name: this.patientProfile.full_name,
      contact_number: this.patientProfile.contact_number,
      email_address: this.patientProfile.email_address,
      date_of_birth: this.patientProfile.date_of_birth,
      gender: this.patientProfile.gender || '',
      blood_group: this.patientProfile.blood_group || '',
      address: this.patientProfile.address || '',
      emergency_contact_name: this.patientProfile.emergency_contact_name || '',
      emergency_contact_number: this.patientProfile.emergency_contact_number || ''
    };
    this.editMode = true;
  }

  cancelEdit() {
    this.editMode = false;
  }

  saveEdit() {
    this.apiService.updatePatient(this.editForm.patient_id, this.editForm).subscribe({
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