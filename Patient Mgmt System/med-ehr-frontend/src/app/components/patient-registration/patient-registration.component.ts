import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-patient-registration',
  templateUrl: './patient-registration.component.html',
  styleUrls: ['./patient-registration.component.css']
})
export class PatientRegistrationComponent implements OnInit {
  patients: any[] = [];
  
  // Form model matching the database fields
  newPatient = {
    patient_id: '',
    full_name: '',
    contact_number: '',
    email_address: '',
    date_of_birth: '',
    gender: '',
    blood_group: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_number: ''
  };

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadPatients();
  }

  loadPatients() {
    this.apiService.getPatients().subscribe(data => {
      this.patients = data;
    });
  }

  registerPatient() {
  this.apiService.registerPatient(this.newPatient).subscribe({
    next: (response) => {
      alert('Patient registered successfully!');
      this.loadPatients();
      this.newPatient = { patient_id: '', full_name: '', contact_number: '', email_address: '', date_of_birth: '', gender: '', blood_group: '', address: '', emergency_contact_name: '', emergency_contact_number: '' };
    },
    error: (err) => {
      console.error('Full error details:', err);
      // This will show you the exact reason from Django in an alert pop-up
      alert('Error: ' + JSON.stringify(err.error));
    }
  });
}
}