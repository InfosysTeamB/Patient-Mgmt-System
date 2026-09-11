import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-patient-book',
  templateUrl: './patient-book.component.html',
  styleUrls: ['./patient-book.component.css']
})
export class PatientBookComponent implements OnInit {
  slots: any[] = [];
  doctors: any[] = [];
  loading = true;
  selectedDate: string = '';
  selectedSlotId: string | null = null;

  timeSlots = [
    { start: '09:00:00', end: '10:00:00', label: '09:00 AM - 10:00 AM' },
    { start: '10:00:00', end: '11:00:00', label: '10:00 AM - 11:00 AM' },
    { start: '11:00:00', end: '12:00:00', label: '11:00 AM - 12:00 PM' },
    { start: '12:00:00', end: '13:00:00', label: '12:00 PM - 01:00 PM' }
  ];
  weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadSlots();
  }

  loadSlots() {
    this.loading = true;
    this.apiService.getDoctors().subscribe(d => this.doctors = d);
    this.apiService.getSlots().subscribe({
      next: (s: any[]) => {
        this.slots = s;
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load slots.');
        this.loading = false;
      }
    });
  }

  getDoctorName(doctorId: string): string {
    const d = this.doctors.find(doc => doc.doctor_id === doctorId);
    return d ? `Dr. ${d.doctor_name}` : '';
  }

  private normalizeTime(t: string): string {
    return (t || '').slice(0, 5);
  }

  getAvailableSlots(): any[] {
    const today = new Date().toISOString().slice(0, 10);
    return this.slots.filter(s =>
      s.status === 'Available' && !s.patient_id &&
      (!s.appointment_date || s.appointment_date >= today)
    );
  }

  getSlotForTimeAndDay(time: string, day: string) {
    return this.slots.find(s =>
      this.normalizeTime(s.start_time) === this.normalizeTime(time) && s.day_of_week === day &&
      (!this.selectedDate || s.appointment_date === this.selectedDate)
    );
  }

  async bookAppointment() {
    if (!this.selectedSlotId) { this.toast.info('Please select a slot to book.'); return; }
    const slot = this.slots.find(s => s.id === this.selectedSlotId);
    if (!slot) { this.toast.error('Slot not found.'); return; }

    const confirmed = await this.confirm.confirm({
      title: 'Confirm Booking',
      message: `Book this appointment with ${this.getDoctorName(slot.doctor_id) || 'your doctor'} on ${slot.appointment_date} (${slot.day_of_week}) at ${slot.start_time}?`,
      confirmText: 'Book Now'
    });
    if (!confirmed) return;

    const payload = {
      patient_id: this.authService.getEntityId(),
      doctor_id: slot.doctor_id,
      day_of_week: slot.day_of_week,
      start_time: slot.start_time,
      end_time: slot.end_time,
      status: 'Booked'
    };

    this.apiService.bookSlot(this.selectedSlotId, payload).subscribe({
      next: () => {
        this.toast.success('Appointment booked successfully!');
        this.loadSlots();
        this.selectedSlotId = null;
      },
      error: () => this.toast.error('Failed to book appointment.')
    });
  }
}