import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-doctor-prescriptions',
  templateUrl: './doctor-prescriptions.component.html',
  styleUrls: ['./doctor-prescriptions.component.css']
})
export class DoctorPrescriptionsComponent implements OnInit {
  prescriptions: any[] = [];
  consultations: any[] = [];
  patients: any[] = [];
  loading = true;
  showCreateForm = false;

  newRx = {
    consultation_id: '',
    instructions: '',
    prescribed_date: new Date().toISOString().slice(0, 10),
    medications: [{ name: '', dosage: '', frequency: '', duration: '', notes: '' }]
  };

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.apiService.getPrescriptions().subscribe({
      next: (r) => { this.prescriptions = r; this.checkDone(); },
      error: () => { this.toast.error('Failed to load prescriptions.'); this.checkDone(); }
    });
    this.apiService.getConsultations().subscribe({
      next: (c) => { this.consultations = c; this.checkDone(); },
      error: () => { this.checkDone(); }
    });
    this.apiService.getPatients().subscribe({
      next: (p) => { this.patients = p; this.checkDone(); },
      error: () => { this.checkDone(); }
    });
  }

  private dataLoaded = 0;
  private checkDone() {
    this.dataLoaded++;
    if (this.dataLoaded >= 3) this.loading = false;
  }

  get sortedPrescriptions(): any[] {
    return [...this.prescriptions].sort((a, b) =>
      (b.prescribed_date || '').localeCompare(a.prescribed_date || '')
    );
  }

  getPatientName(id: string): string {
    const p = this.patients.find(pat => pat.patient_id === id);
    return p ? p.full_name : (id || '—');
  }

  getConsultationLabel(consultationId: string): string {
    const c = this.consultations.find(c => c.consultation_id === consultationId || c.id === consultationId);
    if (!c) return consultationId || '—';
    const patientName = this.getPatientName(c.patient_id);
    return `${patientName} — ${c.consultation_date} — ${c.diagnosis || ''}`;
  }

  getSelectedConsultation(): any {
    return this.consultations.find(c => c.consultation_id === this.newRx.consultation_id || c.id === this.newRx.consultation_id) || null;
  }

  addMedication() {
    this.newRx.medications.push({ name: '', dosage: '', frequency: '', duration: '', notes: '' });
  }

  removeMedication(index: number) {
    if (this.newRx.medications.length > 1) {
      this.newRx.medications.splice(index, 1);
    }
  }

  async createPrescription() {
    if (!this.newRx.consultation_id) {
      this.toast.error('Please select a consultation.');
      return;
    }
    const validMeds = this.newRx.medications.filter(m => m.name.trim());
    if (validMeds.length === 0) {
      this.toast.error('Add at least one medication.');
      return;
    }

    const confirmed = await this.confirm.confirm({
      title: 'Create Prescription',
      message: `Create prescription for ${this.getPatientName(this.getSelectedConsultation()?.patient_id)} with ${validMeds.length} medication(s)?`,
      confirmText: 'Create'
    });
    if (!confirmed) return;

    const payload = { ...this.newRx, medications: validMeds };
    this.apiService.createPrescription(payload).subscribe({
      next: () => {
        this.toast.success('Prescription created!');
        this.showCreateForm = false;
        this.newRx = {
          consultation_id: '',
          instructions: '',
          prescribed_date: new Date().toISOString().slice(0, 10),
          medications: [{ name: '', dosage: '', frequency: '', duration: '', notes: '' }]
        };
        this.loadData();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to create prescription.')
    });
  }

  async deleteRx(rx: any) {
    const confirmed = await this.confirm.confirm({
      title: 'Delete Prescription',
      message: `Delete prescription ${rx.prescription_id}?`,
      confirmText: 'Delete',
      danger: true
    });
    if (!confirmed) return;
    this.apiService.deletePrescription(rx.id).subscribe({
      next: () => { this.toast.success('Deleted.'); this.loadData(); },
      error: () => this.toast.error('Failed to delete.')
    });
  }
}
