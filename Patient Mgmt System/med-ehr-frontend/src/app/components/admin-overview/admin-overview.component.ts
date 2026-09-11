import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-admin-overview',
  templateUrl: './admin-overview.component.html',
  styleUrls: ['./admin-overview.component.css']
})
export class AdminOverviewComponent implements OnInit {
  patientCount = 0;
  doctorCount = 0;
  slotCount = 0;
  bookedCount = 0;
  availableCount = 0;
  statsLoading = true;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.apiService.getPatients().subscribe((p: any[]) => {
      this.patientCount = p.length;
    });
    this.apiService.getDoctors().subscribe((d: any[]) => {
      this.doctorCount = d.length;
    });
    this.apiService.getSlots().subscribe((s: any[]) => {
      this.slotCount = s.length;
      this.bookedCount = s.filter(sl => sl.status === 'Booked').length;
      this.availableCount = s.filter(sl => sl.status === 'Available').length;
      this.statsLoading = false;
    });
  }
}