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
  selectedDoctor: string = '';
  gridDates: string[] = [];

  timeSlots = [
    { start: '09:00:00', end: '10:00:00', label: '09:00 AM - 10:00 AM' },
    { start: '10:00:00', end: '11:00:00', label: '10:00 AM - 11:00 AM' },
    { start: '11:00:00', end: '12:00:00', label: '11:00 AM - 12:00 PM' },
    { start: '12:00:00', end: '13:00:00', label: '12:00 PM - 01:00 PM' }
  ];

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
        this.buildGridDates();
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load slots.');
        this.loading = false;
      }
    });
  }

  buildGridDates() {
    let dateSlots = this.slots;
    if (this.selectedDoctor) {
      dateSlots = dateSlots.filter(s => s.doctor_id === this.selectedDoctor);
    }
    if (this.selectedDate) {
      dateSlots = dateSlots.filter(s => s.appointment_date === this.selectedDate);
    }

    let dates = [...new Set(dateSlots.map(s => s.appointment_date).filter(Boolean))];
    dates.sort();
    this.gridDates = dates;
  }

  getDoctorName(doctorId: string): string {
    const d = this.doctors.find(doc => doc.doctor_id === doctorId);
    return d ? `Dr. ${d.doctor_name}` : '';
  }

  selectDoctor(doctorId: string) {
    this.selectedDoctor = this.selectedDoctor === doctorId ? '' : doctorId;
    this.buildGridDates();
  }

  private normalizeTime(t: string): string {
    return (t || '').slice(0, 5);
  }

  getSlotForTimeAndDate(time: string, date: string) {
    return this.slots.find(s =>
      this.normalizeTime(s.start_time) === this.normalizeTime(time) && s.appointment_date === date &&
      (!this.selectedDoctor || s.doctor_id === this.selectedDoctor)
    );
  }

  formatColumnHeader(date: string): string {
    const d = new Date(date + 'T00:00:00');
    const dayName = d.toLocaleDateString('en-US', { weekday: 'short' });
    const monthDay = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `${dayName}\n${monthDay}`;
  }

  isToday(date: string): boolean {
    return date === new Date().toISOString().slice(0, 10);
  }

  clearFilters() {
    this.selectedDate = '';
    this.selectedDoctor = '';
    this.buildGridDates();
  }

  async bookAppointment(slot: any) {
    if (!slot) return;

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

    this.apiService.bookSlot(slot.id, payload).subscribe({
      next: () => {
        this.toast.success('Appointment booked successfully!');
        this.loadSlots();
      },
      error: () => this.toast.error('Failed to book appointment.')
    });
  }
}