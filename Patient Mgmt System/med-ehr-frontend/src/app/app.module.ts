import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { RoleSelectorComponent } from './components/role-selector/role-selector.component';

// Admin
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard.component';
import { AdminPatientsComponent } from './components/admin-patients/admin-patients.component';
import { AdminDoctorsComponent } from './components/admin-doctors/admin-doctors.component';
import { AdminAppointmentsComponent } from './components/admin-appointments/admin-appointments.component';

// Patient
import { PatientPortalComponent } from './components/patient-portal/patient-portal.component';
import { PatientProfileComponent } from './components/patient-profile/patient-profile.component';
import { PatientBookComponent } from './components/patient-book/patient-book.component';
import { PatientAppointmentsComponent } from './components/patient-appointments/patient-appointments.component';
import { PatientDoctorsComponent } from './components/patient-doctors/patient-doctors.component';

// Doctor
import { DoctorPortalComponent } from './components/doctor-portal/doctor-portal.component';
import { DoctorProfileComponent } from './components/doctor-profile/doctor-profile.component';
import { DoctorScheduleComponent } from './components/doctor-schedule/doctor-schedule.component';
import { DoctorAppointmentsComponent } from './components/doctor-appointments/doctor-appointments.component';

// Shared registrations
import { PatientRegistrationComponent } from './components/patient-registration/patient-registration.component';
import { DoctorRegistrationComponent } from './components/doctor-registration/doctor-registration.component';
import { AppointmentBookingComponent } from './components/appointment-booking/appointment-booking.component';

@NgModule({
  declarations: [
    AppComponent,
    RoleSelectorComponent,
    AdminDashboardComponent,
    AdminPatientsComponent,
    AdminDoctorsComponent,
    AdminAppointmentsComponent,
    PatientPortalComponent,
    PatientProfileComponent,
    PatientBookComponent,
    PatientAppointmentsComponent,
    PatientDoctorsComponent,
    DoctorPortalComponent,
    DoctorProfileComponent,
    DoctorScheduleComponent,
    DoctorAppointmentsComponent,
    PatientRegistrationComponent,
    DoctorRegistrationComponent,
    AppointmentBookingComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
