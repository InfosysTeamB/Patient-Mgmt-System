import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-patient-doctors',
  templateUrl: './patient-doctors.component.html',
  styleUrls: ['./patient-doctors.component.css']
})
export class PatientDoctorsComponent implements OnInit {
  doctors: any[] = [];
  searchTerm: string = '';
  loading = true;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.apiService.getDoctors().subscribe({
      next: (d: any[]) => {
        this.doctors = d;
        this.loading = false;
      },
      error: () => this.loading = false
    });
  }

  get filteredDoctors(): any[] {
    if (!this.searchTerm) return this.doctors;
    const term = this.searchTerm.toLowerCase();
    return this.doctors.filter(d =>
      d.doctor_name.toLowerCase().includes(term) ||
      d.specialization.toLowerCase().includes(term)
    );
  }
}