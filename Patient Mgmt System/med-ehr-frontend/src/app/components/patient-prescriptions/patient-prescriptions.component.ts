import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-patient-prescriptions',
  templateUrl: './patient-prescriptions.component.html',
  styleUrls: ['./patient-prescriptions.component.css']
})
export class PatientPrescriptionsComponent implements OnInit {
  prescriptions: any[] = [];
  doctors: any[] = [];
  loading = true;

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.apiService.getDoctors().subscribe(d => this.doctors = d);
    this.apiService.getPrescriptions().subscribe({
      next: (rxs) => {
        this.prescriptions = rxs;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load prescriptions.');
        this.loading = false;
      }
    });
  }

  getDoctorName(doctorId: string): string {
    const d = this.doctors.find(doc => doc.doctor_id === doctorId);
    return d ? `Dr. ${d.doctor_name}` : (doctorId || '—');
  }

  get sortedPrescriptions(): any[] {
    return [...this.prescriptions].sort((a, b) =>
      (b.prescribed_date || '').localeCompare(a.prescribed_date || '')
    );
  }
}