import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-admin-doctors',
  templateUrl: './admin-doctors.component.html',
  styleUrls: ['./admin-doctors.component.css']
})
export class AdminDoctorsComponent implements OnInit {
  doctors: any[] = [];
  searchTerm: string = '';

  newDoctor = {
    doctor_id: '',
    doctor_name: '',
    specialization: ''
  };

  editingId: string | null = null;
  editForm = { doctor_id: '', doctor_name: '', specialization: '' };

  msg = '';

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadDoctors();
  }

  loadDoctors() {
    this.apiService.getDoctors().subscribe((d: any[]) => this.doctors = d);
  }

  get filteredDoctors(): any[] {
    if (!this.searchTerm) return this.doctors;
    const term = this.searchTerm.toLowerCase();
    return this.doctors.filter(d =>
      d.doctor_name.toLowerCase().includes(term) ||
      d.doctor_id.toLowerCase().includes(term) ||
      (d.specialization || '').toLowerCase().includes(term)
    );
  }

  registerDoctor() {
    this.apiService.registerDoctor(this.newDoctor).subscribe({
      next: () => {
        this.msg = 'Doctor registered successfully!';
        this.newDoctor = { doctor_id: '', doctor_name: '', specialization: '' };
        this.loadDoctors();
      },
      error: (err) => this.msg = err.error?.error || 'Failed to register doctor.'
    });
  }

  startEdit(d: any) {
    this.editingId = d.id;
    this.editForm = {
      doctor_id: d.doctor_id,
      doctor_name: d.doctor_name,
      specialization: d.specialization
    };
  }

  saveEdit() {
    this.apiService.updateDoctor(this.editForm.doctor_id, this.editForm).subscribe({
      next: () => {
        this.msg = 'Doctor updated!';
        this.editingId = null;
        this.loadDoctors();
      },
      error: (err) => this.msg = err.error?.error || 'Failed to update.'
    });
  }

  deleteDoctor(d: any) {
    if (!confirm(`Delete doctor ${d.doctor_name}?`)) return;
    this.apiService.deleteDoctor(d.doctor_id).subscribe({
      next: () => {
        this.msg = 'Doctor deleted.';
        this.loadDoctors();
      },
      error: () => this.msg = 'Failed to delete.'
    });
  }
}
