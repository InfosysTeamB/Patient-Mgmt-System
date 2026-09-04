import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-admin-appointments',
  templateUrl: './admin-appointments.component.html',
  styleUrls: ['./admin-appointments.component.css']
})
export class AdminAppointmentsComponent implements OnInit {
  slots: any[] = [];
  doctors: any[] = [];
  patients: any[] = [];

  timeOptions = [
    { start: '09:00:00', end: '10:00:00', label: '09:00 AM - 10:00 AM' },
    { start: '10:00:00', end: '11:00:00', label: '10:00 AM - 11:00 AM' },
    { start: '11:00:00', end: '12:00:00', label: '11:00 AM - 12:00 PM' },
    { start: '12:00:00', end: '13:00:00', label: '12:00 PM - 01:00 PM' }
  ];
  weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  newSlot = {
    doctor_id: '',
    appointment_date: '',
    day_of_week: '',
    start_time: '',
    end_time: ''
  };

  editingId: string | null = null;
  editForm = {
    doctor_id: '', appointment_date: '', day_of_week: '', start_time: '', end_time: '', status: ''
  };

  msg = '';

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.apiService.getDoctors().subscribe((d: any[]) => this.doctors = d);
    this.apiService.getPatients().subscribe((p: any[]) => this.patients = p);
    this.apiService.getSlots().subscribe((s: any[]) => this.slots = s);
  }

  getDoctorName(id: string): string {
    const d = this.doctors.find(doc => doc.doctor_id === id);
    return d ? `Dr. ${d.doctor_name}` : (id || '—');
  }

  getPatientName(id: string): string {
    const p = this.patients.find(pat => pat.patient_id === id);
    return p ? p.full_name : (id || '—');
  }

  get sortedSlots(): any[] {
    return [...this.slots].sort((a, b) => {
      const da = a.appointment_date || '';
      const db = b.appointment_date || '';
      if (da !== db) return da.localeCompare(db);
      return (a.start_time || '').localeCompare(b.start_time || '');
    });
  }

  createSlot() {
    if (!this.newSlot.doctor_id || !this.newSlot.appointment_date || !this.newSlot.day_of_week || !this.newSlot.start_time || !this.newSlot.end_time) {
      this.msg = 'Please fill in all slot fields.';
      return;
    }
    const payload = { ...this.newSlot, status: 'Available' };
    this.apiService.createSlot(payload).subscribe({
      next: () => {
        this.msg = 'Slot created successfully!';
        this.newSlot = { doctor_id: '', appointment_date: '', day_of_week: '', start_time: '', end_time: '' };
        this.loadData();
      },
      error: (err) => this.msg = err.error?.error || 'Failed to create slot.'
    });
  }

  startEdit(s: any) {
    this.editingId = s.id;
    this.editForm = {
      doctor_id: s.doctor_id,
      appointment_date: s.appointment_date,
      day_of_week: s.day_of_week,
      start_time: s.start_time,
      end_time: s.end_time,
      status: s.status
    };
  }

  saveEdit() {
    this.apiService.updateSlot(this.editingId as string, this.editForm).subscribe({
      next: () => {
        this.msg = 'Slot updated!';
        this.editingId = null;
        this.loadData();
      },
      error: (err) => this.msg = err.error?.error || 'Failed to update.'
    });
  }

  deleteSlot(s: any) {
    if (!confirm('Delete this slot?')) return;
    this.apiService.deleteSlot(s.id).subscribe({
      next: () => {
        this.msg = 'Slot deleted.';
        this.loadData();
      },
      error: () => this.msg = 'Failed to delete.'
    });
  }
}
