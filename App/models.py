from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150)
    is_volunteer = models.BooleanField(default=False)
    is_volunteer_pending = models.BooleanField(default=False)
    phone = models.CharField(max_length=15)
    dob = models.DateField(verbose_name="Date of Birth",blank=True, null=True)
    city = models.CharField(max_length=100,default="Thrissur")
    image = models.ImageField(upload_to="profiles/", blank=True, null=True)


    district = models.CharField(max_length=100)

    local_body = models.CharField(
        max_length=100, 
        help_text="Name of the Panchayat or Municipality",
        default=""
    )
    
    # Address details
    ward_no = models.CharField(max_length=10)
    house_no = models.CharField(max_length=50)
    address = models.TextField(help_text="Full house address/landmark")

    def __str__(self):
        return f"{self.full_name} ({self.district})"

class Condition(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class ReportSubmit(models.Model):

    ANIMAL_TYPE_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('other', 'Other'),
    ]

    LOCATION_SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('gps', 'GPS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('rescued', 'Rescued'),
    
    ]

    animal_type = models.CharField(max_length=10, choices=ANIMAL_TYPE_CHOICES)

    conditions = models.ManyToManyField(Condition, blank=True)

    animal_count = models.PositiveIntegerField(default=1)

    manual_location = models.CharField(
        max_length=255,
        help_text="Road name and nearby landmark"
    )

    auto_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )

    auto_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )

    location_source = models.CharField(
        max_length=10,
        choices=LOCATION_SOURCE_CHOICES,
        default='manual'
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )
    claimed_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='claimed_reports'
)

    claimed_at = models.DateTimeField(
        null=True,
        blank=True
)

    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
)
    user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name="reports"
)
    rescue_image = models.ImageField(
        upload_to="rescue_proof/", 
        null=True, 
        blank=True,
        help_text="Live photo of the animal at the center or safe-zone"
    )
    rescue_notes = models.TextField(blank=True, null=True, help_text="How was the rescue? Any immediate medical needs?")
    rescue_image = models.ImageField(upload_to="rescue_proof/", blank=True, null=True)
        # This acts as your 'Verified' stamp
    is_verified_rescue = models.BooleanField(default=False)

    rescue_notes = models.TextField(
        null=True, 
        blank=True,
        help_text="Details about the animal's current location and condition"
    )

    is_verified_rescue = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
def __str__(self):
        return f"{self.get_animal_type_display()} - {self.manual_location}"


class ReportImage(models.Model):
    report = models.ForeignKey(
        ReportSubmit,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(upload_to="stray_photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Report {self.report.id}"

class Animal(models.Model):
    report = models.OneToOneField(ReportSubmit, on_delete=models.SET_NULL, null=True, blank=True, related_name='animal_profile')
    STATUS_CHOICES = (
        ('Available', 'Available'),
        ('On Process', 'On process of adoption'),
        ('Adopted', 'Adopted'),
    )
    name = models.CharField(max_length=100)
    age = models.CharField(max_length=50, help_text="e.g., 2 years, 6 months")
    breed = models.CharField(max_length=100, blank=True, null=True)
    story = models.TextField()
    health_status = models.TextField(help_text="Vaccination and medical history")
    image = models.ImageField(upload_to='animals/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    in_adoption = models.BooleanField(default=False)  # NEW: prevents duplicate add
    created_at = models.DateTimeField(auto_now_add=True)

    # ... existing fields (report, name, age, breed, etc.) ...
    
    # NEW FIELDS
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    
    CENTER_TYPE_CHOICES = [
        ('ngo', 'NGO'),
        ('government', 'Govt Shelter'),
        ('foster', 'Foster'),
    ]
    center_type = models.CharField(max_length=20, choices=CENTER_TYPE_CHOICES, null=True, blank=True)
    
    # Existing center fields (You may need to add these if they aren't in your Animal model yet)
    center_name = models.CharField(max_length=255, blank=True, null=True)
    center_email = models.EmailField(blank=True, null=True)
    center_phone = models.CharField(max_length=20, blank=True, null=True)
    center_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.status})"

class AdoptionApplication(models.Model):
    STATUS_CHOICES = (
        ('Waiting', 'Waiting for Reply'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Proof_Submitted', 'Proof Submitted'),
        ('Verified', 'Verified'),
    )
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='applications')
    applicant_name = models.CharField(max_length=100)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=20)
    home_environment = models.TextField(help_text="Describe your home, work hours, lifestyle.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Waiting')
    applied_at = models.DateTimeField(auto_now_add=True)

    is_18 = models.CharField(max_length=5, default="yes")
    stable_income = models.CharField(max_length=5, default="yes")
    residence_type = models.CharField(max_length=50, default="house")
    home_ownership = models.CharField(max_length=50, default="owned")
    landlord_permission = models.CharField(max_length=50, default="not_applicable")
    has_pet = models.CharField(max_length=5, default="no")
    current_pet_type = models.CharField(max_length=50, default="none")
    env_quality = models.CharField(max_length=50, default="good")
    amenities = models.CharField(max_length=255, blank=True)

    # Add these to your AdoptionApplication model
    proof_image_1 = models.ImageField(upload_to='adoption_proof/', null=True, blank=True)
    proof_image_2 = models.ImageField(upload_to='adoption_proof/', null=True, blank=True)
    user_notes = models.TextField(blank=True, null=True, help_text="Tell us how the animal is settling in!")
    is_submitted_for_final_verify = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.applicant_name} applying for {self.animal.name}"

class Sponsorship(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='sponsors')
    sponsor_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    donated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sponsor_name} sponsored {self.animal.name}"


from django.db import models

class Organization(models.Model):

    ORG_TYPES = [
        ("ngo", "NGO"),
        ("vet", "Veterinary Clinic"),
        ("adoption", "Adoption Center"),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)

    org_type = models.CharField(max_length=20, choices=ORG_TYPES)

    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    local_body = models.CharField(max_length=100)

    address = models.TextField()

    registration_number = models.CharField(max_length=100)

    image = models.ImageField(upload_to="organizations/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


