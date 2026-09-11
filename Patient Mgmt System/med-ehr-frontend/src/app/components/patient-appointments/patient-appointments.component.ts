import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-patient-appointments',
  templateUrl: './patient-appointments.component.html',
  styleUrls: ['./patient-appointments.component.css']
})
export class PatientAppointmentsComponent implements OnInit {
  myBookings: any[] = [];
  doctors: any[] = [];
  loading = true;

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    const entityId = this.authService.getEntityId();
    this.apiService.getDoctors().subscribe(d => this.doctors = d);
    this.apiService.getSlots().subscribe({
      next: (s: any[]) => {
        this.myBookings = s.filter(sl => sl.patient_id === entityId && sl.status === 'Booked');
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load appointments.');
        this.loading = false;
      }
    });
  }

  getDoctorName(doctorId: string): string {
    const d = this.doctors.find(doc => doc.doctor_id === doctorId);
    return d ? `Dr. ${d.doctor_name}` : doctorId;
  }

  get upcomingBookings(): any[] {
    const today = new Date().toISOString().slice(0, 10);
    return this.myBookings
      .filter(b => b.appointment_date && b.appointment_date >= today)
      .sort((a, b) => (a.appointment_date + a.start_time).localeCompare(b.appointment_date + b.start_time));
  }

  get pastBookings(): any[] {
    const today = new Date().toISOString().slice(0, 10);
    return this.myBookings
      .filter(b => !b.appointment_date || b.appointment_date < today)
      .sort((a, b) => (b.appointment_date + b.start_time).localeCompare(a.appointment_date + a.start_time));
  }

  async cancelBooking(slotId: string) {
    const slot = this.myBookings.find(b => b.id === slotId);
    if (!slot) return;
    const confirmed = await this.confirm.confirm({
      title: 'Cancel Appointment',
      message: `Cancel your appointment with ${this.getDoctorName(slot.doctor_id)} on ${slot.appointment_date} (${slot.day_of_week}) at ${slot.start_time}?`,
      confirmText: 'Cancel Appointment',
      danger: true
    });
    if (!confirmed) return;
    const payload = {
      patient_id: null,
      status: 'Available'
    };
    this.apiService.bookSlot(slotId, payload).subscribe({
      next: () => {
        this.toast.success('Appointment cancelled.');
        this.loadData();
      },
      error: () => this.toast.error('Failed to cancel.')
    });
  }
}