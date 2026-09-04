import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-patient-profile',
  templateUrl: './patient-profile.component.html',
  styleUrls: ['./patient-profile.component.css']
})
export class PatientProfileComponent implements OnInit {
  patientProfile: any = null;
  editMode = false;
  editForm = {
    patient_id: '',
    full_name: '',
    contact_number: '',
    email_address: '',
    date_of_birth: ''
  };
  msg = '';

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile() {
    const entityId = this.authService.getEntityId();
    this.apiService.getPatients().subscribe((data: any[]) => {
      this.patientProfile = data.find(p => p.patient_id === entityId) || null;
    });
  }

  startEdit() {
    if (!this.patientProfile) return;
    this.editForm = {
      patient_id: this.patientProfile.patient_id,
      full_name: this.patientProfile.full_name,
      contact_number: this.patientProfile.contact_number,
      email_address: this.patientProfile.email_address,
      date_of_birth: this.patientProfile.date_of_birth
    };
    this.editMode = true;
    this.msg = '';
  }

  cancelEdit() {
    this.editMode = false;
    this.msg = '';
  }

  saveEdit() {
    this.apiService.updatePatient(this.editForm.patient_id, this.editForm).subscribe({
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
