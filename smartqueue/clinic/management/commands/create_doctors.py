from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clinic.models import Department, DoctorTimeSlot
from datetime import time

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates departments and doctors with their time slots'

    def handle(self, *args, **kwargs):
        # Create departments
        departments = [
            'Cardiology',
            'Neurology',
            'Orthopedics',
            'Pediatrics',
            'Dermatology',
            'Ophthalmology',
            'ENT',
            'General Medicine'
        ]

        for dept_name in departments:
            Department.objects.get_or_create(name=dept_name)
            self.stdout.write(f'Created department: {dept_name}')

        # Create doctors for each department
        doctors_data = {
            'Cardiology': [
                {'username': 'dr.smith', 'first_name': 'John', 'last_name': 'Smith', 'email': 'dr.smith@clinic.com'},
                {'username': 'dr.johnson', 'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'dr.johnson@clinic.com'}
            ],
            'Neurology': [
                {'username': 'dr.williams', 'first_name': 'Michael', 'last_name': 'Williams', 'email': 'dr.williams@clinic.com'},
                {'username': 'dr.brown', 'first_name': 'Emily', 'last_name': 'Brown', 'email': 'dr.brown@clinic.com'}
            ],
            'Orthopedics': [
                {'username': 'dr.davis', 'first_name': 'Robert', 'last_name': 'Davis', 'email': 'dr.davis@clinic.com'},
                {'username': 'dr.miller', 'first_name': 'Lisa', 'last_name': 'Miller', 'email': 'dr.miller@clinic.com'}
            ],
            'Pediatrics': [
                {'username': 'dr.wilson', 'first_name': 'David', 'last_name': 'Wilson', 'email': 'dr.wilson@clinic.com'},
                {'username': 'dr.moore', 'first_name': 'Jennifer', 'last_name': 'Moore', 'email': 'dr.moore@clinic.com'}
            ],
            'Dermatology': [
                {'username': 'dr.taylor', 'first_name': 'James', 'last_name': 'Taylor', 'email': 'dr.taylor@clinic.com'},
                {'username': 'dr.anderson', 'first_name': 'Patricia', 'last_name': 'Anderson', 'email': 'dr.anderson@clinic.com'}
            ],
            'Ophthalmology': [
                {'username': 'dr.thomas', 'first_name': 'Richard', 'last_name': 'Thomas', 'email': 'dr.thomas@clinic.com'},
                {'username': 'dr.jackson', 'first_name': 'Mary', 'last_name': 'Jackson', 'email': 'dr.jackson@clinic.com'}
            ],
            'ENT': [
                {'username': 'dr.white', 'first_name': 'Charles', 'last_name': 'White', 'email': 'dr.white@clinic.com'},
                {'username': 'dr.harris', 'first_name': 'Elizabeth', 'last_name': 'Harris', 'email': 'dr.harris@clinic.com'}
            ],
            'General Medicine': [
                {'username': 'dr.martin', 'first_name': 'Joseph', 'last_name': 'Martin', 'email': 'dr.martin@clinic.com'},
                {'username': 'dr.thompson', 'first_name': 'Margaret', 'last_name': 'Thompson', 'email': 'dr.thompson@clinic.com'}
            ]
        }

        # Create doctors and their time slots
        for dept_name, doctors in doctors_data.items():
            department = Department.objects.get(name=dept_name)
            for doctor_info in doctors:
                # Create doctor user
                doctor, created = User.objects.get_or_create(
                    username=doctor_info['username'],
                    defaults={
                        'email': doctor_info['email'],
                        'first_name': doctor_info['first_name'],
                        'last_name': doctor_info['last_name'],
                        'role': 'doctor',
                        'department': department,
                        'is_staff': True
                    }
                )
                
                if created:
                    doctor.set_password('doctor123')  # Set a default password
                    doctor.save()
                    self.stdout.write(f'Created doctor: Dr. {doctor_info["first_name"]} {doctor_info["last_name"]}')

                    # Create time slots for the doctor
                    time_slots = [
                        (time(9, 0), time(10, 0)),   # 9:00 AM - 10:00 AM
                        (time(10, 0), time(11, 0)),  # 10:00 AM - 11:00 AM
                        (time(11, 0), time(12, 0)),  # 11:00 AM - 12:00 PM
                        (time(14, 0), time(15, 0)),  # 2:00 PM - 3:00 PM
                        (time(15, 0), time(16, 0)),  # 3:00 PM - 4:00 PM
                        (time(16, 0), time(17, 0))   # 4:00 PM - 5:00 PM
                    ]

                    for start_time, end_time in time_slots:
                        DoctorTimeSlot.objects.create(
                            doctor=doctor,
                            start_time=start_time,
                            end_time=end_time
                        )
                    self.stdout.write(f'Created time slots for Dr. {doctor_info["first_name"]} {doctor_info["last_name"]}')

        self.stdout.write(self.style.SUCCESS('Successfully created all departments and doctors')) 