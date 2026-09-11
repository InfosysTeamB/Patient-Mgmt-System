import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = '/api';

  constructor(private http: HttpClient) { }

  // Auth methods
  login(credentials: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/login/`, credentials);
  }

  registerUser(userData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/register/`, userData);
  }

  // Patient methods
  getPatients(): Observable<any> {
    return this.http.get(`${this.baseUrl}/patients/`);
  }

  registerPatient(patientData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/patients/`, patientData);
  }

  updatePatient(patientId: string, patientData: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/patients/${patientId}/`, patientData);
  }

  deletePatient(patientId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/patients/${patientId}/`);
  }

  // Doctor methods
  getDoctors(): Observable<any> {
    return this.http.get(`${this.baseUrl}/doctors/`);
  }

  registerDoctor(doctorData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/doctors/`, doctorData);
  }

  updateDoctor(doctorId: string, doctorData: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/doctors/${doctorId}/`, doctorData);
  }

  deleteDoctor(doctorId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/doctors/${doctorId}/`);
  }

  // Slot methods
  getSlots(): Observable<any> {
    return this.http.get(`${this.baseUrl}/slots/`);
  }

  createSlot(slotData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/slots/`, slotData);
  }

  updateSlot(slotId: string, slotData: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/slots/${slotId}/`, slotData);
  }

  deleteSlot(slotId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/slots/${slotId}/`);
  }

  bookSlot(slotId: string, bookingData: any): Observable<any> {
    return this.http.patch(`${this.baseUrl}/slots/${slotId}/`, bookingData);
  }

  // Consultation methods
  getConsultations(): Observable<any> {
    return this.http.get(`${this.baseUrl}/consultations/`);
  }

  getConsultation(consultationId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/consultations/${consultationId}/`);
  }

  createConsultation(data: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/consultations/`, data);
  }

  updateConsultation(consultationId: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/consultations/${consultationId}/`, data);
  }

  // Prescription methods
  getPrescriptions(): Observable<any> {
    return this.http.get(`${this.baseUrl}/prescriptions/`);
  }

  getPrescription(prescriptionId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/prescriptions/${prescriptionId}/`);
  }

  createPrescription(data: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/prescriptions/`, data);
  }

  updatePrescription(prescriptionId: string, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/prescriptions/${prescriptionId}/`, data);
  }

  deletePrescription(prescriptionId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/prescriptions/${prescriptionId}/`);
  }

  // Treatment history
  getTreatmentHistory(patientId: string): Observable<any> {
    return this.http.get(`${this.baseUrl}/treatment-history/${patientId}/`);
  }
}