import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-patient-appointments',
  templateUrl: './patient-appointments.component.html',
  styleUrls: ['./patient-appointments.component.css']
})
export class PatientAppointmentsComponent implements OnInit {
  myBookings: any[] = [];
  doctors: any[] = [];

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    const entityId = this.authService.getEntityId();
    this.apiService.getDoctors().subscribe((d: any[]) => this.doctors = d);
    this.apiService.getSlots().subscribe((s: any[]) => {
      this.myBookings = s.filter(sl => sl.patient_id === entityId && sl.status === 'Booked');
    });
  }

  getDoctorName(doctorId: string): string {
    const d = this.doctors.find(doc => doc.doctor_id === doctorId);
    return d ? `Dr. ${d.doctor_name}` : doctorId;
  }

  cancelBooking(slotId: string) {
    const slot = this.myBookings.find(b => b.id === slotId);
    if (!slot) return;
    const payload = {
      patient_id: null,
      status: 'Available'
    };
    this.apiService.bookSlot(slotId, payload).subscribe({
      next: () => {
        alert('Appointment cancelled.');
        this.loadData();
      },
      error: () => alert('Failed to cancel.')
    });
  }
}
