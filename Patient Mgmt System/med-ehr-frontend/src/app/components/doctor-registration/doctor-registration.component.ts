import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-doctor-registration',
  templateUrl: './doctor-registration.component.html',
  styleUrls: ['./doctor-registration.component.css']
})
export class DoctorRegistrationComponent implements OnInit {
  doctors: any[] = [];

  newDoctor = {
    doctor_id: '',
    doctor_name: '',
    specialization: ''
  };

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadDoctors();
  }

  loadDoctors() {
    this.apiService.getDoctors().subscribe(data => {
      this.doctors = data;
    });
  }

  registerDoctor() {
    this.apiService.registerDoctor(this.newDoctor).subscribe({
      next: () => {
        alert('Doctor registered successfully!');
        this.loadDoctors();
        this.newDoctor = { doctor_id: '', doctor_name: '', specialization: '' };
      },
      error: (err) => {
        console.error(err);
        alert('Error: ' + JSON.stringify(err.error));
      }
    });
  }
}
