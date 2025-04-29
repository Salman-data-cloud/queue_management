from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import CustomUserCreationForm, AppointmentForm, FeedbackForm
from .models import Appointment, User, Feedback, DoctorTimeSlot, Department
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'clinic/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
        else:
            return render(request, 'clinic/login.html', {'error_message': 'Invalid username or password'})
    return render(request, 'clinic/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'clinic/dashboard.html')

@login_required
def book_appointment(request):
    if request.user.role != 'patient':
        return redirect('dashboard')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            appointment_date = form.cleaned_data['date_time']
            time_slot = form.cleaned_data['time_slot']
            patient = request.user
            if appointment_date - timezone.now() < timedelta(days=3):
                form.add_error('date_time', 'Appointment must be at least 3 days in advance.')
                return render(request, 'clinic/book_appointment.html', {'form': form})
            doctor_appointments = Appointment.objects.filter(doctor = doctor,
                                                             date_time__date=appointment_date.date(), status='pending').count()
            
            if doctor_appointments >= 10:
                form.add_error('doctor', 'Doctor is fully booked for the day.')
                return render(request, 'clinic/book_appointment.html', {'form': form})
            
            patient_appointments = Appointment.objects.filter(patient=patient,
                                                               date_time__date=appointment_date.date(), status='pending')
            if patient_appointments.count()>2:
                form.add_error(None, 'You can only book 2 doctors per day.')
                return render(request, 'clinic/book_appointment.html', {'form': form})
            
            for i in patient_appointments:
                if i.doctor.department == doctor.department:
                    form.add_error('doctor', 'You already have an appointment with a doctor from this department.')
                    return render(request, 'clinic/book_appointment.html', {'form': form})

            for i in patient_appointments:
                if i.date_time == appointment_date:
                    form.add_error('date_time', 'You already have an appointment at this time.')
                    return render(request, 'clinic/book_appointment.html', {'form': form})
                
            if Appointment.objects.filter(doctor=doctor, appointment_date= datetime.date(), time_slot=time_slot).exists():
                form.add_error('time_slot', 'This doctor is already booked for this time slot.')
                return render(request, 'clinic/book_appointment.html', {'form': form})

            appointment = form.save(commit=False)
            appointment.patient = request.user 
            if appointment.doctor == request.user:
                form.add_error('doctor', 'You cannot book an appointment with yourself.')
                return render(request, 'clinic/book_appointment.html', {'form': form})
            appointment.token_number = generate_token_number(appointment.doctor)
            appointment.save()
            return redirect('dashboard')
    else:
        form = AppointmentForm()
    return render(request, 'clinic/book_appointment.html', {'form': form})

@login_required
def give_feedback(request):
    if request.user.role != 'patient':
        return redirect('dashboard')
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.patient = request.user
            feedback.save()
            return redirect('dashboard')
    else:
        form = FeedbackForm()
    return render(request, 'clinic/give_feedback.html', {'form': form})

def generate_token_number(doctor):
    last_appointment = Appointment.objects.filter(doctor=doctor).order_by('-token_number').first()
    if last_appointment:
        return last_appointment.token_number + 1
    return 1

def update_token_status():
    now = timezone.now()
    pending_appointments = Appointment.objects.filter(status='pending', date_time__lt=now)
    for appointment in pending_appointments:
        appointment.status = 'missed'
        appointment.save()

# doctor dashboard view
@login_required
def doctor_dashboard(request):
    if request.user.role != 'doctor':
        return redirect('dashboard')
    
    update_token_status()
    
    appointments = Appointment.objects.filter(doctor=request.user, status='pending').order_by('token_number')
    
    return render(request, 'clinic/doctor_dashboard/doctor_dashboard.html', {'appointments': appointments})

def prioritize_patient(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.is_priority = True
    appointment.save()
    return redirect('doctor_dashboard')

def mark_visited(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.status = 'visited'
    appointment.save()
    return redirect('doctor_dashboard')

def skip_patient(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.status = 'skipped'
    appointment.save()
    return redirect('doctor_dashboard')

# admin dashboard view
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    total_appointments = Appointment.objects.count()
    visited = Appointment.objects.filter(status='visited').count()
    missed = Appointment.objects.filter(status='missed').count()
    skipped = Appointment.objects.filter(status='skipped').count()
    
    context = {
        'total': total_appointments,
        'visited': visited,
        'missed': missed,
        'skipped': skipped,
    }
    
    return render(request,'admin_dashboard/admin_dashboard.html', context)

