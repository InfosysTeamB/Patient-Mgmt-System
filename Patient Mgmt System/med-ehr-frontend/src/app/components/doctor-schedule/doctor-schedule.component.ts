import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-doctor-schedule',
  templateUrl: './doctor-schedule.component.html',
  styleUrls: ['./doctor-schedule.component.css']
})
export class DoctorScheduleComponent implements OnInit {
  mySlots: any[] = [];

  timeSlots = [
    { start: '09:00:00', end: '10:00:00', label: '09:00 AM - 10:00 AM' },
    { start: '10:00:00', end: '11:00:00', label: '10:00 AM - 11:00 AM' },
    { start: '11:00:00', end: '12:00:00', label: '11:00 AM - 12:00 PM' },
    { start: '12:00:00', end: '13:00:00', label: '12:00 PM - 01:00 PM' }
  ];
  weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  newSlot = {
    appointment_date: '',
    day_of_week: '',
    start_time: '',
    end_time: ''
  };
  msg = '';

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    this.loadSlots();
  }

  loadSlots() {
    const entityId = this.authService.getEntityId();
    this.apiService.getSlots().subscribe((s: any[]) => {
      this.mySlots = s.filter(sl => sl.doctor_id === entityId);
    });
  }

  getSlotForTimeAndDay(time: string, day: string) {
    return this.mySlots.find(s => s.start_time === time && s.day_of_week === day);
  }

  createSlot() {
    if (!this.newSlot.appointment_date || !this.newSlot.day_of_week || !this.newSlot.start_time || !this.newSlot.end_time) {
      this.msg = 'Please fill in all slot fields.';
      return;
    }
    const payload = {
      ...this.newSlot,
      doctor_id: this.authService.getEntityId(),
      status: 'Available'
    };
    this.apiService.createSlot(payload).subscribe({
      next: () => {
        this.msg = 'Slot created successfully!';
        this.newSlot = { appointment_date: '', day_of_week: '', start_time: '', end_time: '' };
        this.loadSlots();
      },
      error: (err) => {
        this.msg = err.error?.error || 'Failed to create slot.';
      }
    });
  }

  deleteSlot(slotId: string) {
    if (!confirm('Delete this slot?')) return;
    this.apiService.deleteSlot(slotId).subscribe({
      next: () => {
        this.msg = 'Slot deleted.';
        this.loadSlots();
      },
      error: () => this.msg = 'Failed to delete slot.'
    });
  }
}
