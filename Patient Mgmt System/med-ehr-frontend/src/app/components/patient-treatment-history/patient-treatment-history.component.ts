import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';

@Component({
  selector: 'app-patient-treatment-history',
  templateUrl: './patient-treatment-history.component.html',
  styleUrls: ['./patient-treatment-history.component.css']
})
export class PatientTreatmentHistoryComponent implements OnInit {
  records: any[] = [];
  doctors: any[] = [];
  loading = true;

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    const patientId = this.authService.getEntityId();
    this.apiService.getDoctors().subscribe(d => this.doctors = d);
    this.apiService.getTreatmentHistory(patientId).subscribe({
      next: (records) => {
        this.records = records;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load treatment history.');
        this.loading = false;
      }
    });
  }

  getDoctorName(doctorId: string): string {
    const d = this.doctors.find(doc => doc.doctor_id === doctorId);
    return d ? `Dr. ${d.doctor_name}` : (doctorId || '—');
  }

  get sortedRecords(): any[] {
    return [...this.records].sort((a, b) => {
      const da = a.consultation_date || a.prescribed_date || '';
      const db = b.consultation_date || b.prescribed_date || '';
      return db.localeCompare(da);
    });
  }

  getDate(r: any): string {
    return r.consultation_date || r.prescribed_date || '—';
  }
}