from django.core.management.base import BaseCommand
from clinic.views import send_appointment_reminders

class Command(BaseCommand):
    help = 'Sends appointment reminders for tomorrow\'s appointments'

    def handle(self, *args, **options):
        try:
            send_appointment_reminders()
            self.stdout.write(self.style.SUCCESS('Successfully sent appointment reminders'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending reminders: {str(e)}')) 