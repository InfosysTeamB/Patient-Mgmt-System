import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-admin-patients',
  templateUrl: './admin-patients.component.html',
  styleUrls: ['./admin-patients.component.css']
})
export class AdminPatientsComponent implements OnInit {
  patients: any[] = [];
  searchTerm: string = '';

  newPatient = {
    patient_id: '',
    full_name: '',
    contact_number: '',
    email_address: '',
    date_of_birth: ''
  };

  editingId: string | null = null;
  editForm = { patient_id: '', full_name: '', contact_number: '', email_address: '', date_of_birth: '' };

  msg = '';

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadPatients();
  }

  loadPatients() {
    this.apiService.getPatients().subscribe((d: any[]) => this.patients = d);
  }

  get filteredPatients(): any[] {
    if (!this.searchTerm) return this.patients;
    const term = this.searchTerm.toLowerCase();
    return this.patients.filter(p =>
      p.full_name.toLowerCase().includes(term) ||
      p.patient_id.toLowerCase().includes(term) ||
      (p.email_address || '').toLowerCase().includes(term)
    );
  }

  registerPatient() {
    this.apiService.registerPatient(this.newPatient).subscribe({
      next: () => {
        this.msg = 'Patient registered successfully!';
        this.newPatient = { patient_id: '', full_name: '', contact_number: '', email_address: '', date_of_birth: '' };
        this.loadPatients();
      },
      error: (err) => this.msg = err.error?.error || 'Failed to register patient.'
    });
  }

  startEdit(p: any) {
    this.editingId = p.id;
    this.editForm = {
      patient_id: p.patient_id,
      full_name: p.full_name,
      contact_number: p.contact_number,
      email_address: p.email_address,
      date_of_birth: p.date_of_birth
    };
  }

  saveEdit() {
    this.apiService.updatePatient(this.editForm.patient_id, this.editForm).subscribe({
      next: () => {
        this.msg = 'Patient updated!';
        this.editingId = null;
        this.loadPatients();
      },
      error: (err) => this.msg = err.error?.error || 'Failed to update.'
    });
  }

  deletePatient(p: any) {
    if (!confirm(`Delete patient ${p.full_name}?`)) return;
    this.apiService.deletePatient(p.patient_id).subscribe({
      next: () => {
        this.msg = 'Patient deleted.';
        this.loadPatients();
      },
      error: () => this.msg = 'Failed to delete.'
    });
  }
}
