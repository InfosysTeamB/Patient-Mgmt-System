import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-doctor-schedule',
  templateUrl: './doctor-schedule.component.html',
  styleUrls: ['./doctor-schedule.component.css']
})
export class DoctorScheduleComponent implements OnInit {
  mySlots: any[] = [];
  loading = true;
  gridDates: string[] = [];
  fromDate: string = '';
  toDate: string = '';

  timeSlots = [
    { start: '09:00:00', end: '10:00:00', label: '09:00 AM - 10:00 AM' },
    { start: '10:00:00', end: '11:00:00', label: '10:00 AM - 11:00 AM' },
    { start: '11:00:00', end: '12:00:00', label: '11:00 AM - 12:00 PM' },
    { start: '12:00:00', end: '13:00:00', label: '12:00 PM - 01:00 PM' }
  ];

  newSlot = {
    appointment_date: '',
    day_of_week: '',
    start_time: '',
    end_time: ''
  };

  constructor(private apiService: ApiService, private authService: AuthService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadSlots();
  }

  loadSlots() {
    this.loading = true;
    const entityId = this.authService.getEntityId();
    this.apiService.getSlots().subscribe({
      next: (s: any[]) => {
        this.mySlots = s.filter(sl => sl.doctor_id === entityId);
        this.buildGridDates();
        this.loading = false;
      },
      error: () => {
        this.toast.error('Failed to load schedule.');
        this.loading = false;
      }
    });
  }

  buildGridDates() {
    let dates = [...new Set(this.mySlots.map(s => s.appointment_date).filter(Boolean))];
    if (this.fromDate) {
      dates = dates.filter(d => d >= this.fromDate);
    }
    if (this.toDate) {
      dates = dates.filter(d => d <= this.toDate);
    }
    dates.sort();
    if (dates.length > 0) {
      this.gridDates = dates;
    } else if (this.fromDate || this.toDate) {
      this.gridDates = this.mySlots.length > 0 ? [] : this.getNextWeekdays(5);
    } else {
      this.gridDates = this.getNextWeekdays(5);
    }
  }

  private getNextWeekdays(count: number): string[] {
    const result: string[] = [];
    const d = new Date();
    while (result.length < count) {
      const day = d.getDay();
      if (day !== 0 && day !== 6) {
        result.push(d.toISOString().slice(0, 10));
      }
      d.setDate(d.getDate() + 1);
    }
    return result;
  }

  getSlotForTimeAndDate(time: string, date: string) {
    const t = (time || '').slice(0, 5);
    return this.mySlots.find(s =>
      (s.start_time || '').slice(0, 5) === t && s.appointment_date === date
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
    this.fromDate = '';
    this.toDate = '';
    this.buildGridDates();
  }

  getPatientName(slot: any): string {
    if (slot.patient_details && slot.patient_details.full_name) {
      return slot.patient_details.full_name;
    }
    return slot.patient_id || '';
  }

  createSlot() {
    if (!this.newSlot.appointment_date || !this.newSlot.start_time || !this.newSlot.end_time) {
      this.toast.error('Please fill in all slot fields.');
      return;
    }
    const d = new Date(this.newSlot.appointment_date + 'T00:00:00');
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    this.newSlot.day_of_week = dayNames[d.getDay()];

    const payload = {
      ...this.newSlot,
      doctor_id: this.authService.getEntityId(),
      status: 'Available'
    };
    this.apiService.createSlot(payload).subscribe({
      next: () => {
        this.toast.success('Slot created successfully!');
        this.newSlot = { appointment_date: '', day_of_week: '', start_time: '', end_time: '' };
        this.loadSlots();
      },
      error: (err) => {
        this.toast.error(err.error?.error || 'Failed to create slot.');
      }
    });
  }

  async deleteSlot(slot: any) {
    const confirmed = await this.confirm.confirm({
      title: 'Delete Slot',
      message: `Delete the ${slot.appointment_date} ${slot.start_time} slot?`,
      confirmText: 'Delete',
      danger: true
    });
    if (!confirmed) return;
    this.apiService.deleteSlot(slot.id).subscribe({
      next: () => {
        this.toast.success('Slot deleted.');
        this.loadSlots();
      },
      error: () => this.toast.error('Failed to delete slot.')
    });
  }
}
