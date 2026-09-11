import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-patient-overview',
  templateUrl: './patient-overview.component.html',
  styleUrls: ['./patient-overview.component.css']
})
export class PatientOverviewComponent implements OnInit {
  userName = '';
  upcomingCount = 0;
  nextAppointment: any = null;
  loading = true;

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.userName = this.authService.getUser()?.name || 'Patient';
    const entityId = this.authService.getEntityId();
    this.apiService.getSlots().subscribe((s: any[]) => {
      const bookings = s.filter(sl => sl.patient_id === entityId && sl.status === 'Booked');
      this.upcomingCount = bookings.length;
      const today = new Date().toISOString().slice(0, 10);
      const upcoming = bookings
        .filter(b => b.appointment_date && b.appointment_date >= today)
        .sort((a, b) => (a.appointment_date + a.start_time).localeCompare(b.appointment_date + b.start_time));
      this.nextAppointment = upcoming[0] || null;
      this.loading = false;
    });
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