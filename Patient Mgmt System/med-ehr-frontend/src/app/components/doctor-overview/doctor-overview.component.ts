import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-doctor-overview',
  templateUrl: './doctor-overview.component.html',
  styleUrls: ['./doctor-overview.component.css']
})
export class DoctorOverviewComponent implements OnInit {
  userName = '';
  totalSlots = 0;
  todayAppointments: any[] = [];
  patients: any[] = [];
  loading = true;

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.userName = this.authService.getUser()?.name || 'Doctor';
    const entityId = this.authService.getEntityId();
    const today = new Date().toISOString().slice(0, 10);

    this.apiService.getPatients().subscribe((p: any[]) => this.patients = p);
    this.apiService.getSlots().subscribe((s: any[]) => {
      const myBooked = s.filter(sl => sl.doctor_id === entityId && sl.status === 'Booked');
      this.totalSlots = s.filter(sl => sl.doctor_id === entityId).length;
      this.todayAppointments = myBooked
        .filter(sl => sl.appointment_date === today)
        .sort((a, b) => a.start_time.localeCompare(b.start_time));
      this.loading = false;
    });
  }

  getPatientName(id: string): string {
    const p = this.patients.find(pat => pat.patient_id === id);
    return p ? p.full_name : id;
  }

  formatTime(t: string): string {
    if (!t) return '';
    const [h, m] = t.split(':');
    const hour = parseInt(h, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${m} ${ampm}`;
  }
}