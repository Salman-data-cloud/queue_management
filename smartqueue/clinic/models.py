from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('visited', 'Visited'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
    )
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    date_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    token_number = models.PositiveIntegerField()
    is_priority = models.BooleanField(default=False)

    def __str__(self):
        return f"Appointment {self.id} - {self.patient} with {self.doctor} on {self.date_time}"

class Feedback(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_feedbacks')
    rating = models.IntegerField()
    comment = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.patient} for {self.doctor} ({self.rating})"