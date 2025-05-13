from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import CustomUserCreationForm, AppointmentForm, FeedbackForm, MedicalRecordForm
from .models import Appointment, User, Feedback, DoctorTimeSlot, Department, MedicalRecord
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
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
            if user.is_superuser:
                return redirect('admin_dashboard')
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
    user = request.user
    today = timezone.localtime().date()
    print('DEBUG: Today according to server:', today)
    print('DEBUG: All appointments for today:')
    for a in Appointment.objects.filter(date_time__date=today):
        print(f'ID: {a.id}, Date: {a.date_time}, Doctor: {a.doctor}, Patient: {a.patient}, Status: {a.status}')
    
    if user.role == 'patient':
        appointments = Appointment.objects.filter(
            patient=user,
            date_time__date=today
        ).order_by('token_number')
    elif user.role == 'doctor':
        appointments = Appointment.objects.filter(
            doctor=user,
            date_time__date=today
        ).order_by('token_number')
    else:  # admin
        appointments = Appointment.objects.filter(
            date_time__date=today
        ).order_by('token_number')
    
    waiting_count = appointments.filter(status='pending').count()
    visited_count = appointments.filter(status='visited').count()
    priority_count = appointments.filter(is_priority=True).count()
    
    context = {
        'appointments': appointments,
        'waiting_count': waiting_count,
        'visited_count': visited_count,
        'priority_count': priority_count,
        'today': today,
    }
    
    return render(request, 'clinic/dashboard.html', context)

@login_required
def book_appointment(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST' and is_ajax:
        # Handle AJAX requests for dynamic form updates
        if 'department' in request.POST:
            department_id = request.POST.get('department')
            doctors = User.objects.filter(role='doctor', department_id=department_id)
            return JsonResponse({
                'doctors': [{'id': doctor.id, 'name': doctor.get_full_name() or doctor.username} for doctor in doctors]
            })
        elif 'doctor' in request.POST:
            doctor_id = request.POST.get('doctor')
            time_slots = DoctorTimeSlot.objects.filter(doctor_id=doctor_id)
            return JsonResponse({
                'time_slots': [{'id': slot.id, 'start_time': slot.start_time.strftime('%H:%M'), 
                               'end_time': slot.end_time.strftime('%H:%M')} for slot in time_slots]
            })

    if request.user.role != 'patient':
        return redirect('dashboard')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            appointment_date = form.cleaned_data['date_time']
            time_slot = form.cleaned_data['time_slot']
            patient = request.user

            # Combine the date from the form with the time from the time slot
            appointment_datetime = datetime.combine(appointment_date.date(), time_slot.start_time)
            
            doctor_appointments = Appointment.objects.filter(
                doctor=doctor,
                date_time__date=appointment_date.date(), 
                status='pending'
            ).count()
            
            if doctor_appointments >= 10:
                form.add_error('doctor', 'Doctor is fully booked for the day.')
                return render(request, 'clinic/book_appointment.html', {'form': form})
            
            patient_appointments = Appointment.objects.filter(
                patient=patient,
                date_time__date=appointment_date.date(), 
                status='pending'
            )
            if patient_appointments.count() > 2:
                form.add_error(None, 'You can only book 2 doctors per day.')
                return render(request, 'clinic/book_appointment.html', {'form': form})
            
            for i in patient_appointments:
                if i.doctor.department == doctor.department:
                    form.add_error('doctor', 'You already have an appointment with a doctor from this department.')
                    return render(request, 'clinic/book_appointment.html', {'form': form})

            for i in patient_appointments:
                if i.date_time == appointment_datetime:
                    form.add_error('date_time', 'You already have an appointment at this time.')
                    return render(request, 'clinic/book_appointment.html', {'form': form})
                
            # Check if doctor has any appointment at the same time
            if Appointment.objects.filter(
                doctor=doctor,
                date_time__date=appointment_date.date(),
                date_time__time__gte=time_slot.start_time,
                date_time__time__lt=time_slot.end_time,
                status='pending'
            ).exists():
                form.add_error('date_time', 'This doctor is already booked for this time slot.')
                return render(request, 'clinic/book_appointment.html', {'form': form})

            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.date_time = timezone.make_aware(appointment_datetime)  # Set the combined date and time as timezone-aware
            if appointment.doctor == request.user:
                form.add_error('doctor', 'You cannot book an appointment with yourself.')
                return render(request, 'clinic/book_appointment.html', {'form': form})
            appointment.token_number = generate_token_number(appointment.doctor)
            appointment.save()

            # Send confirmation email with token number
            subject = 'Appointment Confirmation - Smart Queue Clinic'
            html_message = render_to_string('clinic/email/appointment_confirmation.html', {
                'appointment': appointment,
                'token_number': appointment.token_number
            })
            
            send_mail(
                subject=subject,
                message='',  # Plain text version (empty as we're using HTML)
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[appointment.patient.email],
                html_message=html_message,
                fail_silently=False,
            )

            # Handle medical record upload if provided
            if 'medical_record' in request.FILES:
                medical_record = MedicalRecord(
                    patient=request.user,
                    appointment=appointment,
                    file=request.FILES['medical_record'],
                    description=request.POST.get('medical_record_description', '')
                )
                medical_record.save()

            return render(request, 'clinic/booking_success.html', {
                'appointment': appointment,
                'token_number': appointment.token_number
            })
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
    today = timezone.localtime().date()
    print('DEBUG: Today according to server:', today)
    print('DEBUG: All appointments for today (doctor):')
    for a in Appointment.objects.filter(date_time__date=today):
        print(f'ID: {a.id}, Date: {a.date_time}, Doctor: {a.doctor}, Patient: {a.patient}, Status: {a.status}')
    
    appointments = Appointment.objects.filter(
        doctor=request.user,
        date_time__date=today
    ).order_by('token_number')
    
    waiting_count = appointments.filter(status='pending').count()
    visited_count = appointments.filter(status='visited').count()
    priority_count = appointments.filter(is_priority=True).count()
    
    context = {
        'appointments': appointments,
        'waiting_count': waiting_count,
        'visited_count': visited_count,
        'priority_count': priority_count,
        'today': today,
    }
    
    return render(request, 'clinic/doctor_dashboard/doctor_dashboard.html', context)

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
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return redirect('dashboard')
    today = timezone.localtime().date()
    today = timezone.now().date()
    appointments = Appointment.objects.filter(date_time__date=today).order_by('token_number')
    total_appointments = appointments.count()
    visited = appointments.filter(status='visited').count()
    missed = appointments.filter(status='missed').count()
    skipped = appointments.filter(status='skipped').count()
    waiting_count = appointments.filter(status='pending').count()
    priority_count = appointments.filter(is_priority=True).count()
    context = {
        'total': total_appointments,
        'visited': visited,
        'missed': missed,
        'skipped': skipped,
        'appointments': appointments,
        'waiting_count': waiting_count,
        'priority_count': priority_count,
    }
    return render(request, 'admin_dashboard/admin_dashboard.html', context)

@login_required
def queue_status(request):
    user = request.user
    today = timezone.now().date()
    
    if user.role == 'doctor':
        appointments = Appointment.objects.filter(
            doctor=user,
            date_time__date=today
        ).order_by('token_number')
    elif user.role == 'patient':
        appointments = Appointment.objects.filter(
            patient=user,
            date_time__date=today
        ).order_by('token_number')
    else:  # admin
        appointments = Appointment.objects.filter(
            date_time__date=today
        ).order_by('token_number')
    
    waiting_count = appointments.filter(status='pending').count()
    visited_count = appointments.filter(status='visited').count()
    priority_count = appointments.filter(is_priority=True).count()
    
    data = {
        'appointments': [
            {
                'token_number': app.token_number,
                'patient_name': app.patient.get_full_name() or app.patient.username,
                'time': app.date_time.strftime('%I:%M %p'),
                'status': app.status,
                'is_priority': app.is_priority
            }
            for app in appointments
        ],
        'stats': {
            'waiting': waiting_count,
            'visited': visited_count,
            'priority': priority_count
        }
    }
    
    return JsonResponse(data)

def send_appointment_reminder(appointment):
    """Send appointment reminder email to patient"""
    subject = 'Appointment Reminder - Smart Queue Clinic'
    
    # Render email template
    html_message = render_to_string('clinic/email/appointment_reminder.html', {
        'appointment': appointment
    })
    
    # Send email
    send_mail(
        subject=subject,
        message='',  # Plain text version (empty as we're using HTML)
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[appointment.patient.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_appointment_reminders():
    """Send reminders for appointments scheduled for tomorrow"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    # Get all appointments for tomorrow
    appointments = Appointment.objects.filter(
        date_time__date=tomorrow,
        status='pending'  # Only send reminders for pending appointments
    )
    
    for appointment in appointments:
        send_appointment_reminder(appointment)

@login_required
def doctor_analytics(request):
    if request.user.role != 'doctor':
        return redirect('dashboard')
    return render(request, 'clinic/doctor_dashboard/doctor_analytics.html')

@login_required
def doctor_settings(request):
    if request.user.role != 'doctor':
        return redirect('dashboard')
    return render(request, 'clinic/doctor_dashboard/doctor_settings.html')

@login_required
def upload_medical_record(request, appointment_id):
    if request.user.role != 'patient':
        return redirect('dashboard')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id, patient=request.user)
    except Appointment.DoesNotExist:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = request.user
            medical_record.appointment = appointment
            medical_record.save()
            return redirect('dashboard')
    else:
        form = MedicalRecordForm()
    
    return render(request, 'clinic/upload_medical_record.html', {
        'form': form,
        'appointment': appointment
    })

@login_required
def view_medical_records(request, appointment_id):
    if request.user.role != 'doctor':
        return redirect('dashboard')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id, doctor=request.user)
        medical_records = MedicalRecord.objects.filter(appointment=appointment)
    except Appointment.DoesNotExist:
        return redirect('dashboard')
    
    return render(request, 'clinic/view_medical_records.html', {
        'appointment': appointment,
        'medical_records': medical_records
    })

