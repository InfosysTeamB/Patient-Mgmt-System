import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-doctor-consultations',
  templateUrl: './doctor-consultations.component.html',
  styleUrls: ['./doctor-consultations.component.css']
})
export class DoctorConsultationsComponent implements OnInit {
  slots: any[] = [];
  patients: any[] = [];
  loading = true;

  completingSlotId: string | null = null;
  consultationForm = { diagnosis: '', notes: '' };

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    const entityId = this.authService.getEntityId();
    this.apiService.getPatients().subscribe(p => this.patients = p);
    this.apiService.getSlots().subscribe({
      next: (s: any[]) => {
        this.slots = s.filter(sl => sl.doctor_id === entityId);
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load data.');
        this.loading = false;
      }
    });
  }

  getPatientName(patientId: string): string {
    const p = this.patients.find(pat => pat.patient_id === patientId);
    return p ? p.full_name : (patientId || '—');
  }

  get bookedSlots(): any[] {
    return this.slots
      .filter(s => s.status === 'Booked')
      .sort((a, b) => (a.appointment_date || '').localeCompare(b.appointment_date || ''));
  }

  get completedSlots(): any[] {
    return this.slots
      .filter(s => s.status === 'Completed')
      .sort((a, b) => (b.appointment_date || '').localeCompare(a.appointment_date || ''));
  }

  startComplete(slot: any) {
    this.completingSlotId = slot.id;
    this.consultationForm = { diagnosis: '', notes: '' };
  }

  async completeConsultation(slot: any) {
    if (!this.consultationForm.diagnosis.trim()) {
      this.toast.error('Diagnosis is required.');
      return;
    }
    const confirmed = await this.confirm.confirm({
      title: 'Complete Consultation',
      message: `Complete consultation for ${this.getPatientName(slot.patient_id)} on ${slot.appointment_date}?`,
      confirmText: 'Complete',
      danger: true
    });
    if (!confirmed) return;

    this.apiService.bookSlot(slot.id, {
      status: 'Completed',
      consultation: this.consultationForm
    }).subscribe({
      next: () => {
        this.toast.success('Consultation completed!');
        this.completingSlotId = null;
        this.loadData();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to complete consultation.')
    });
  }
}
