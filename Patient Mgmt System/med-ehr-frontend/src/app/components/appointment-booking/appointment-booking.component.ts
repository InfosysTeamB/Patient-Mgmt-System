import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-appointment-booking',
  templateUrl: './appointment-booking.component.html',
  styleUrls: ['./appointment-booking.component.css']
})
export class AppointmentBookingComponent implements OnInit {
  patients: any[] = [];
  doctors: any[] = [];
  slots: any[] = [];

  // Form selections
  selectedDate: string = '';
  selectedPatientId: string = '';
  selectedDoctorId: string = '';
  selectedSlotId: string | null = null;

  // New slot form
  newSlot = {
    doctor_id: '',
    appointment_date: '',
    day_of_week: '',
    start_time: '',
    end_time: ''
  };

  // Time rows for our grid view
  timeSlots = [
    { start: '09:00:00', end: '10:00:00', label: '09:00 AM - 10:00 AM' },
    { start: '10:00:00', end: '11:00:00', label: '10:00 AM - 11:00 AM' },
    { start: '11:00:00', end: '12:00:00', label: '11:00 AM - 12:00 PM' },
    { start: '12:00:00', end: '13:00:00', label: '12:00 PM - 01:00 PM' }
  ];

  weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
  // Fetch patients and log results to debug
  this.apiService.getPatients().subscribe({
    next: (data) => {
      this.patients = data;
      console.log('Loaded Patients:', this.patients);
    },
    error: (err) => console.error('Error loading patients:', err)
  });

  // Fetch doctors
  this.apiService.getDoctors().subscribe({
    next: (data) => {
      this.doctors = data;
      console.log('Loaded Doctors:', this.doctors);
    },
    error: (err) => console.error('Error loading doctors:', err)
  });

  // Fetch slots
  this.apiService.getSlots().subscribe({
    next: (data) => {
      this.slots = data;
      console.log('Loaded Slots:', this.slots);
    },
    error: (err) => console.error('Error loading slots:', err)
  });
}

  // Find slot status for a specific day and time based on selected date
  getSlotForTimeAndDay(time: string, day: string) {
    return this.slots.find(s => 
      s.start_time === time && 
      s.day_of_week === day && 
      (!this.selectedDate || s.appointment_date === this.selectedDate)
    );
  }

  createSlot() {
    if (!this.newSlot.doctor_id || !this.newSlot.appointment_date || !this.newSlot.day_of_week || !this.newSlot.start_time || !this.newSlot.end_time) {
      alert('Please fill in all slot fields.');
      return;
    }

    const payload = {
      ...this.newSlot,
      status: 'Available'
    };

    this.apiService.createSlot(payload).subscribe({
      next: () => {
        alert('Slot created successfully!');
        this.loadData();
        this.newSlot = { doctor_id: '', appointment_date: '', day_of_week: '', start_time: '', end_time: '' };
      },
      error: (err) => {
        console.error(err);
        alert('Error creating slot: ' + JSON.stringify(err.error));
      }
    });
  }

  bookAppointment() {
    if (!this.selectedSlotId || !this.selectedPatientId) {
      alert('Please select a Patient and an Available Slot from the dropdown.');
      return;
    }

    const slot = this.slots.find(s => s.id === this.selectedSlotId);
    if (!slot) {
      alert('Selected slot not found.');
      return;
    }

    const payload = {
      patient_id: this.selectedPatientId,
      doctor_id: slot.doctor_id,
      day_of_week: slot.day_of_week,
      start_time: slot.start_time,
      end_time: slot.end_time,
      status: 'Booked'
    };

    this.apiService.bookSlot(this.selectedSlotId, payload).subscribe({
      next: () => {
        alert('Appointment successfully booked!');
        this.loadData();
        this.selectedSlotId = null;
      },
      error: (err) => {
        console.error(err);
        alert('Failed to book appointment.');
      }
    });
  }
}