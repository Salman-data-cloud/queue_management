from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Appointment, Feedback, Department, DoctorTimeSlot

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user
class AppointmentForm(forms.ModelForm):
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True)
    time_slot = forms.ModelChoiceField(queryset=DoctorTimeSlot.objects.none(), required=True, label="Available Time Slot")
    class Meta:
        model = Appointment
        fields = ('department', 'doctor', 'date_time', 'time_slot')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['doctor'].queryset = User.objects.filter(role='doctor', department_id=department_id)
            except (ValueError, TypeError):
                self.fields['doctor'].queryset = User.objects.none()

        elif self.instance.pk and self.instance.doctor:
            self.fields['doctor'].queryset = User.objects.filter(role='doctor', department=self.instance.doctor.department)
        else:
            self.fields['doctor'].queryset = User.objects.none()

        if 'doctor' in self.data:
            try:
                doctor_id = int(self.data.get('doctor'))
                self.fields['time_slot'].queryset = DoctorTimeSlot.objects.filter(doctor_id=doctor_id)
            except (ValueError, TypeError):
                self.fields['time_slot'].queryset = DoctorTimeSlot.objects.none()

        elif self.instance.pk and self.instance.doctor:
            self.fields['time_slot'].queryset = DoctorTimeSlot.objects.filter(doctor=self.instance.doctor)

        else:
            self.fields['time_slot'].queryset = DoctorTimeSlot.objects.none()
            
class FeedbackForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.NumberInput(attrs={'placeholder': '1-5'}))

    class Meta:
        model = Feedback
        fields = ('doctor', 'rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your feedback'}),
        }

