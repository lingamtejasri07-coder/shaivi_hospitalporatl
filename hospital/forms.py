from django import forms
from django.utils import timezone
from .models import Doctor, Patient, Appointment, MedicalReport


class AppointmentBookingForm(forms.ModelForm):
    # Patient fields embedded for smooth single-page booking
    patient_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. John Doe',
            'id': 'patient_name'
        }),
        label="Full Name"
    )
    patient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'id': 'patient_email'
        }),
        label="Email Address"
    )
    patient_phone = forms.CharField(
        max_length=25,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1 (555) 234-5678',
            'id': 'patient_phone'
        }),
        label="Phone Number"
    )
    gender = forms.ChoiceField(
        choices=Patient.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'patient_gender'
        }),
        label="Gender"
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'patient_dob'
        }),
        label="Date of Birth"
    )
    blood_group = forms.ChoiceField(
        choices=[('', '-- Select Blood Group (Optional) --')] + Patient.BLOOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'patient_blood'
        }),
        label="Blood Group"
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time_slot', 'reason']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-select', 'id': 'doctor_select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'appointment_date'}),
            'time_slot': forms.Select(attrs={'class': 'form-select', 'id': 'time_slot_select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Please describe symptoms, purpose of visit, or primary concern...',
                'id': 'appointment_reason'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only active doctors can be booked
        self.fields['doctor'].queryset = Doctor.objects.filter(active_status=True)
        self.fields['doctor'].empty_label = "-- Choose a Specialist --"
        self.fields['time_slot'].choices = [('', '-- Choose a Time Slot --')] + Appointment.TIME_SLOTS

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.localdate():
            raise forms.ValidationError("Appointment date cannot be in the past. Please select a current or future date.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        time_slot = cleaned_data.get('time_slot')

        if doctor and date and time_slot:
            # Check double booking
            overlapping = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time_slot=time_slot
            ).exclude(status='Cancelled')

            if overlapping.exists():
                raise forms.ValidationError(
                    f"Dr. {doctor.name} is already booked for {time_slot} on {date}. "
                    "Please choose another time slot or date."
                )

        return cleaned_data


class AppointmentStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional internal notes...'}),
        }


class MedicalReportForm(forms.ModelForm):
    class Meta:
        model = MedicalReport
        fields = ['diagnosis', 'treatment_plan', 'notes', 'follow_up_date']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter diagnosed condition...'}),
            'treatment_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Prescriptions, recommended medicines, tests...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dietary guidelines, precautions, notes...'}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = [
            'name', 'department', 'specialization', 'consultation_fee', 
            'available_days', 'qualification', 'experience_years', 'room_number', 
            'email', 'phone', 'bio', 'active_status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mon, Wed, Fri'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'active_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
