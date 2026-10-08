from django.contrib import admin
from .models import Doctor, Patient, Appointment, MedicalReport


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'specialization', 'consultation_fee', 'available_days', 'active_status')
    list_filter = ('department', 'active_status')
    search_fields = ('name', 'specialization', 'department')
    list_editable = ('active_status', 'consultation_fee')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'department', 'specialization', 'qualification', 'experience_years')
        }),
        ('Practice Details', {
            'fields': ('consultation_fee', 'available_days', 'room_number', 'active_status')
        }),
        ('Contact & Bio', {
            'fields': ('email', 'phone', 'bio')
        }),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'gender', 'blood_group', 'created_at')
    list_filter = ('gender', 'blood_group', 'created_at')
    search_fields = ('name', 'email', 'phone')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'patient', 'doctor', 'date', 'time_slot', 'status', 'created_date')
    list_filter = ('status', 'doctor__department', 'date', 'doctor')
    search_fields = ('tracking_code', 'patient__name', 'patient__email', 'doctor__name', 'reason')
    list_editable = ('status',)
    date_hierarchy = 'date'
    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    @admin.action(description="Mark selected appointments as Confirmed")
    def mark_confirmed(self, request, queryset):
        queryset.update(status='Confirmed')

    @admin.action(description="Mark selected appointments as Completed")
    def mark_completed(self, request, queryset):
        queryset.update(status='Completed')

    @admin.action(description="Mark selected appointments as Cancelled")
    def mark_cancelled(self, request, queryset):
        queryset.update(status='Cancelled')


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'follow_up_date', 'created_date')
    list_filter = ('doctor', 'created_date')
    search_fields = ('patient__name', 'doctor__name', 'diagnosis', 'treatment_plan')
