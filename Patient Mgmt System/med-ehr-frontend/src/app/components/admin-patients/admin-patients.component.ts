import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-admin-patients',
  templateUrl: './admin-patients.component.html',
  styleUrls: ['./admin-patients.component.css']
})
export class AdminPatientsComponent implements OnInit {
  patients: any[] = [];
  searchTerm: string = '';
  loading = true;

  newPatient = {
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

  editingId: string | null = null;
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

  constructor(private apiService: ApiService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadPatients();
  }

  loadPatients() {
    this.loading = true;
    this.apiService.getPatients().subscribe({
      next: (d: any[]) => {
        this.patients = d;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load patients.');
        this.loading = false;
      }
    });
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
      next: (res: any) => {
        this.toast.success('Patient registered successfully!');
        if (res && res.login_created) {
          this.toast.info(`Login created: ${this.newPatient.email_address} / medehr@123`);
        }
        this.newPatient = { patient_id: '', full_name: '', contact_number: '', email_address: '', date_of_birth: '', gender: '', blood_group: '', address: '', emergency_contact_name: '', emergency_contact_number: '' };
        this.loadPatients();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to register patient.')
    });
  }

  startEdit(p: any) {
    this.editingId = p.id;
    this.editForm = {
      patient_id: p.patient_id,
      full_name: p.full_name,
      contact_number: p.contact_number,
      email_address: p.email_address,
      date_of_birth: p.date_of_birth,
      gender: p.gender || '',
      blood_group: p.blood_group || '',
      address: p.address || '',
      emergency_contact_name: p.emergency_contact_name || '',
      emergency_contact_number: p.emergency_contact_number || ''
    };
  }

  saveEdit() {
    this.apiService.updatePatient(this.editForm.patient_id, this.editForm).subscribe({
      next: () => {
        this.toast.success('Patient updated!');
        this.editingId = null;
        this.loadPatients();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to update.')
    });
  }

  async deletePatient(p: any) {
    const confirmed = await this.confirm.confirm({
      title: 'Delete Patient',
      message: `Are you sure you want to delete patient ${p.full_name}? This action cannot be undone.`,
      confirmText: 'Delete',
      danger: true
    });
    if (!confirmed) return;
    this.apiService.deletePatient(p.patient_id).subscribe({
      next: () => {
        this.toast.success('Patient deleted.');
        this.loadPatients();
      },
      error: () => this.toast.error('Failed to delete.')
    });
  }
}