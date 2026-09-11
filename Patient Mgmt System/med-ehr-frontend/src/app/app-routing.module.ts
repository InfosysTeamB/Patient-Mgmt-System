import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { RoleSelectorComponent } from './components/role-selector/role-selector.component';

// Admin
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard.component';
import { AdminPatientsComponent } from './components/admin-patients/admin-patients.component';
import { AdminDoctorsComponent } from './components/admin-doctors/admin-doctors.component';
import { AdminAppointmentsComponent } from './components/admin-appointments/admin-appointments.component';
import { AdminOverviewComponent } from './components/admin-overview/admin-overview.component';

// Patient
import { PatientPortalComponent } from './components/patient-portal/patient-portal.component';
import { PatientProfileComponent } from './components/patient-profile/patient-profile.component';
import { PatientBookComponent } from './components/patient-book/patient-book.component';
import { PatientAppointmentsComponent } from './components/patient-appointments/patient-appointments.component';
import { PatientDoctorsComponent } from './components/patient-doctors/patient-doctors.component';
import { PatientOverviewComponent } from './components/patient-overview/patient-overview.component';

// Doctor
import { DoctorPortalComponent } from './components/doctor-portal/doctor-portal.component';
import { DoctorProfileComponent } from './components/doctor-profile/doctor-profile.component';
import { DoctorScheduleComponent } from './components/doctor-schedule/doctor-schedule.component';
import { DoctorAppointmentsComponent } from './components/doctor-appointments/doctor-appointments.component';
import { DoctorOverviewComponent } from './components/doctor-overview/doctor-overview.component';

const routes: Routes = [
  { path: '', component: RoleSelectorComponent },

  // Admin
  {
    path: 'admin',
    component: AdminDashboardComponent,
    children: [
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      { path: 'overview', component: AdminOverviewComponent },
      { path: 'patients', component: AdminPatientsComponent },
      { path: 'doctors', component: AdminDoctorsComponent },
      { path: 'appointments', component: AdminAppointmentsComponent },
    ]
  },

  // Patient
  {
    path: 'patient',
    component: PatientPortalComponent,
    children: [
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      { path: 'overview', component: PatientOverviewComponent },
      { path: 'profile', component: PatientProfileComponent },
      { path: 'book', component: PatientBookComponent },
      { path: 'appointments', component: PatientAppointmentsComponent },
      { path: 'doctors', component: PatientDoctorsComponent },
    ]
  },

  // Doctor
  {
    path: 'doctor',
    component: DoctorPortalComponent,
    children: [
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      { path: 'overview', component: DoctorOverviewComponent },
      { path: 'profile', component: DoctorProfileComponent },
      { path: 'schedule', component: DoctorScheduleComponent },
      { path: 'appointments', component: DoctorAppointmentsComponent },
    ]
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
