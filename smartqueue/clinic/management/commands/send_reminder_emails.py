from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from clinic.models import Appointment
from datetime import timedelta
from django.utils import timezone
from clinic.models import Appointment
from django.core.mail import send_mail

class Command(BaseCommand):
    help = 'Send email reminders for tomorrow appointments'

    def handle(self, *args, **kwargs):
        tomorrow = timezone.now() + timedelta(days=1)
        start_of_day = tomorrow.replace(hour=0, minute=0, second=0)
        end_of_day = tomorrow.replace(hour=23, minute=59, second=59)
        
        appointments = Appointment.objects.filter(date_time__range=(start_of_day, end_of_day), status='pending')
        
        for appointment in appointments:
            send_mail(
                subject='Appointment Reminder - Your Clinic',
                message=f'Dear {appointment.patient.username},\n\nThis is a reminder that you have an appointment tomorrow at {appointment.date_time.strftime("%I:%M %p")}.\n\nThank you!',
                from_email='yourclinicemail@gmail.com',
                recipient_list=[appointment.patient.email],
                fail_silently=False,
            )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {appointments.count()} reminders.'))
