from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from clinic.models import User

class Command(BaseCommand):
    help = 'Resets passwords for all doctors to a specified password'

    def add_arguments(self, parser):
        parser.add_argument('new_password', type=str, help='The new password to set for all doctors')

    def handle(self, *args, **options):
        new_password = options['new_password']
        doctors = User.objects.filter(role='doctor')
        
        if not doctors.exists():
            self.stdout.write(self.style.WARNING('No doctors found in the system.'))
            return
        
        # Update all doctors' passwords
        doctors.update(password=make_password(new_password))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully reset passwords for {doctors.count()} doctors to: {new_password}'
            )
        ) 