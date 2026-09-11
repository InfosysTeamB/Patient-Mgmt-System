import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-doctor-appointments',
  templateUrl: './doctor-appointments.component.html',
  styleUrls: ['./doctor-appointments.component.css']
})
export class DoctorAppointmentsComponent implements OnInit {
  myAppointments: any[] = [];
  expandedPatientId: string | null = null;
  loading = true;

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    const entityId = this.authService.getEntityId();
    this.apiService.getSlots().subscribe({
      next: (s: any[]) => {
        const mySlots = s.filter(sl => sl.doctor_id === entityId);
        this.myAppointments = mySlots
          .filter(sl => sl.status === 'Booked')
          .sort((a, b) => (a.appointment_date || '').localeCompare(b.appointment_date || ''));
        this.loading = false;
      },
      error: () => this.loading = false
    });
  }

  getPatientDetails(patientId: string): any {
    const appt = this.myAppointments.find(a => a.patient_id === patientId);
    return appt ? appt.patient_details : null;
  }

  getPatientName(patientId: string): string {
    const details = this.getPatientDetails(patientId);
    return details ? details.full_name : (patientId || 'Unknown');
  }

  toggleDetails(patientId: string): void {
    this.expandedPatientId = this.expandedPatientId === patientId ? null : patientId;
  }
}