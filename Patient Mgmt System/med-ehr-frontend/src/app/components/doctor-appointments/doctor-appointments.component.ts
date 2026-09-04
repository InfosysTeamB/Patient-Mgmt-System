import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-doctor-appointments',
  templateUrl: './doctor-appointments.component.html',
  styleUrls: ['./doctor-appointments.component.css']
})
export class DoctorAppointmentsComponent implements OnInit {
  myAppointments: any[] = [];
  patients: any[] = [];

  constructor(private apiService: ApiService, private authService: AuthService) {}

  ngOnInit(): void {
    const entityId = this.authService.getEntityId();
    this.apiService.getPatients().subscribe((p: any[]) => this.patients = p);
    this.apiService.getSlots().subscribe((s: any[]) => {
      const mySlots = s.filter(sl => sl.doctor_id === entityId);
      this.myAppointments = mySlots.filter(sl => sl.status === 'Booked');
    });
  }

  getPatientName(patientId: string): string {
    const p = this.patients.find(pat => pat.patient_id === patientId);
    return p ? p.full_name : patientId;
  }

  getPatientContact(patientId: string): string {
    const p = this.patients.find(pat => pat.patient_id === patientId);
    return p ? p.contact_number : '-';
  }
}
