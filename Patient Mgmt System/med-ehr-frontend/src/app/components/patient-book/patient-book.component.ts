import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-patient-book',
  templateUrl: './patient-book.component.html',
  styleUrls: ['./patient-book.component.css']
})
export class PatientBookComponent implements OnInit {
  slots: any[] = [];
  selectedDate: string = '';
  selectedSlotId: string | null = null;

  timeSlots = [
    { start: '09:00:00', end: '10:00:00', label: '09:00 AM - 10:00 AM' },
    { start: '10:00:00', end: '11:00:00', label: '10:00 AM - 11:00 AM' },
    { start: '11:00:00', end: '12:00:00', label: '11:00 AM - 12:00 PM' },
    { start: '12:00:00', end: '13:00:00', label: '12:00 PM - 01:00 PM' }
  ];
  weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.loadSlots();
  }

  loadSlots() {
    this.apiService.getSlots().subscribe((s: any[]) => this.slots = s);
  }

  getSlotForTimeAndDay(time: string, day: string) {
    return this.slots.find(s =>
      s.start_time === time && s.day_of_week === day &&
      (!this.selectedDate || s.appointment_date === this.selectedDate)
    );
  }

  bookAppointment() {
    if (!this.selectedSlotId) { alert('Please select a slot to book.'); return; }
    const slot = this.slots.find(s => s.id === this.selectedSlotId);
    if (!slot) { alert('Slot not found.'); return; }

    const payload = {
      patient_id: this.authService.getEntityId(),
      doctor_id: slot.doctor_id,
      day_of_week: slot.day_of_week,
      start_time: slot.start_time,
      end_time: slot.end_time,
      status: 'Booked'
    };

    this.apiService.bookSlot(this.selectedSlotId, payload).subscribe({
      next: () => { alert('Appointment booked!'); this.loadSlots(); this.selectedSlotId = null; },
      error: () => alert('Failed to book.')
    });
  }
}
