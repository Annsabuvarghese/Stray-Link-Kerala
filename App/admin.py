from django.contrib import admin
from .models import (
    Profile, Condition, ReportSubmit, ReportImage, 
    Animal, AdoptionApplication, Sponsorship
)

# --- Inline for Report Images ---
# This allows you to see/upload images directly inside the Report page
class ReportImageInline(admin.TabularInline):
    model = ReportImage
    extra = 1

# --- Profile Admin ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'district', 'phone', 'dob')
    search_fields = ('full_name', 'user__username', 'phone', 'district')
    list_filter = ('district',)

# --- Report Admin ---
@admin.register(ReportSubmit)
class ReportSubmitAdmin(admin.ModelAdmin):
    list_display = ('animal_type', 'status', 'manual_location', 'reporter', 'created_at')
    list_filter = ('status', 'animal_type', 'created_at', 'location_source')
    search_fields = ('manual_location', 'reporter__username')
    inlines = [ReportImageInline]
    filter_horizontal = ('conditions',) # Makes selecting multiple conditions easier

# --- Animal Admin ---
@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'center_name', 'center_email', 'in_adoption', 'created_at')
    list_filter = ('status', 'center_type', 'gender', 'in_adoption')
    search_fields = ('name', 'center_name', 'breed')
    readonly_fields = ('created_at',)

# --- Adoption Application Admin ---
@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant_name', 'animal', 'status', 'applied_at', 'env_quality')
    list_filter = ('status', 'residence_type', 'has_pet', 'is_18')
    search_fields = ('applicant_name', 'applicant_email', 'animal__name')
    
    # Organizing the detailed questionnaire into sections
    fieldsets = (
        ('Basic Information', {
            'fields': ('animal', 'status', 'applicant_name', 'applicant_email', 'applicant_phone')
        }),
        ('Eligibility Details', {
            'fields': ('is_18', 'stable_income', 'income_source', 'income_amount')
        }),
        ('Home Environment', {
            'fields': ('residence_type', 'home_ownership', 'landlord_permission', 'env_quality', 'home_environment')
        }),
        ('Pet History', {
            'fields': ('has_pet', 'current_pet_type')
        }),
    )

# --- Sponsorship Admin ---
@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ('sponsor_name', 'animal', 'amount', 'donated_at')
    list_filter = ('donated_at',)
    search_fields = ('sponsor_name', 'animal__name')

# --- Simple Registrations ---
admin.site.register(Condition)
admin.site.register(ReportImage)