import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { ToastService } from '../../services/toast.service';
import { ConfirmService } from '../../services/confirm.service';

@Component({
  selector: 'app-admin-appointments',
  templateUrl: './admin-appointments.component.html',
  styleUrls: ['./admin-appointments.component.css']
})
export class AdminAppointmentsComponent implements OnInit {
  slots: any[] = [];
  doctors: any[] = [];
  patients: any[] = [];
  loading = true;
  dataLoaded = 0;

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

  filterDoctor = '';
  filterDate = '';
  filterStatus = '';

  editingId: string | null = null;
  editForm = {
    doctor_id: '', appointment_date: '', day_of_week: '', start_time: '', end_time: '', status: ''
  };

  constructor(private apiService: ApiService, private toast: ToastService, private confirm: ConfirmService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.dataLoaded = 0;
    this.apiService.getDoctors().subscribe(d => {
      this.doctors = d;
      this.checkLoaded();
    });
    this.apiService.getPatients().subscribe(p => {
      this.patients = p;
      this.checkLoaded();
    });
    this.apiService.getSlots().subscribe(s => {
      this.slots = s;
      this.checkLoaded();
    });
  }

  checkLoaded() {
    this.dataLoaded++;
    if (this.dataLoaded >= 3) {
      this.loading = false;
    }
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
    return [...this.slots]
      .filter(s =>
        (!this.filterDoctor || s.doctor_id === this.filterDoctor) &&
        (!this.filterDate || s.appointment_date === this.filterDate) &&
        (!this.filterStatus || s.status === this.filterStatus)
      )
      .sort((a, b) => {
        const da = a.appointment_date || '';
        const db = b.appointment_date || '';
        if (da !== db) return da.localeCompare(db);
        return (a.start_time || '').localeCompare(b.start_time || '');
      });
  }

  clearFilters() {
    this.filterDoctor = '';
    this.filterDate = '';
    this.filterStatus = '';
  }

  createSlot() {
    if (!this.newSlot.doctor_id || !this.newSlot.appointment_date || !this.newSlot.day_of_week || !this.newSlot.start_time || !this.newSlot.end_time) {
      this.toast.error('Please fill in all slot fields.');
      return;
    }
    const payload = { ...this.newSlot, status: 'Available' };
    this.apiService.createSlot(payload).subscribe({
      next: () => {
        this.toast.success('Slot created successfully!');
        this.newSlot = { doctor_id: '', appointment_date: '', day_of_week: '', start_time: '', end_time: '' };
        this.loadData();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to create slot.')
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
        this.toast.success('Slot updated!');
        this.editingId = null;
        this.loadData();
      },
      error: (err) => this.toast.error(err.error?.error || 'Failed to update.')
    });
  }

  async deleteSlot(s: any) {
    const confirmed = await this.confirm.confirm({
      title: 'Delete Slot',
      message: `Delete the ${s.day_of_week} ${s.start_time} slot? This action cannot be undone.`,
      confirmText: 'Delete',
      danger: true
    });
    if (!confirmed) return;
    this.apiService.deleteSlot(s.id).subscribe({
      next: () => {
        this.toast.success('Slot deleted.');
        this.loadData();
      },
      error: () => this.toast.error('Failed to delete.')
    });
  }
}