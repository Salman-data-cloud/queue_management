from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Appointment, Feedback

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('doctor', 'date_time')


class FeedbackForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.NumberInput(attrs={'placeholder': '1-5'}))

    class Meta:
        model = Feedback
        fields = ('doctor', 'rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your feedback'}),
        }

