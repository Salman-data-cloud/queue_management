from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Removes all registered users except superusers'

    def handle(self, *args, **kwargs):
        # Get all non-superuser users
        users_to_delete = User.objects.filter(is_superuser=False)
        count = users_to_delete.count()
        
        # Delete the users
        users_to_delete.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} users. Superusers remain unchanged.')
        ) 