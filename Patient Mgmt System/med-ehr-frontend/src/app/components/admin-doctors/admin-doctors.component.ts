import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-admin-doctors',
  templateUrl: './admin-doctors.component.html',
  styleUrls: ['./admin-doctors.component.css']
})
export class AdminDoctorsComponent implements OnInit {
  doctors: any[] = [];
  searchTerm: string = '';
  loading = true;

  newDoctor = {
    doctor_id: '',
    doctor_name: '',
    specialization: '',
    email_address: ''
  };

  editingId: string | null = null;
  editForm = { doctor_id: '', doctor_name: '', specialization: '', email_address: '' };

  constructor(private apiService: ApiService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadDoctors();
  }

  loadDoctors() {
    this.loading = true;
    this.apiService.getDoctors().subscribe({
      next: (d: any[]) => {
        this.doctors = d;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load doctors.');
        this.loading = false;
      }
    });
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
      next: (res: any) => {
        this.toast.success('Doctor registered successfully!');
        if (res && res.login_created) {
          this.toast.info(`Login created: ${this.newDoctor.email_address} / medehr@123`);
        }
        this.newDoctor = { doctor_id: '', doctor_name: '', specialization: '', email_address: '' };
        this.loadDoctors();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to register doctor.')
    });
  }

  startEdit(d: any) {
    this.editingId = d.id;
    this.editForm = {
      doctor_id: d.doctor_id,
      doctor_name: d.doctor_name,
      specialization: d.specialization,
      email_address: d.email_address || ''
    };
  }

  saveEdit() {
    this.apiService.updateDoctor(this.editForm.doctor_id, this.editForm).subscribe({
      next: () => {
        this.toast.success('Doctor updated!');
        this.editingId = null;
        this.loadDoctors();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to update.')
    });
  }

  async deleteDoctor(d: any) {
    const confirmed = await this.confirm.confirm({
      title: 'Delete Doctor',
      message: `Are you sure you want to delete Dr. ${d.doctor_name}? This action cannot be undone.`,
      confirmText: 'Delete',
      danger: true
    });
    if (!confirmed) return;
    this.apiService.deleteDoctor(d.doctor_id).subscribe({
      next: () => {
        this.toast.success('Doctor deleted.');
        this.loadDoctors();
      },
      error: () => this.toast.error('Failed to delete.')
    });
  }
}