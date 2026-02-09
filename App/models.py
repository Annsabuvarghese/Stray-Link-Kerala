from django.db import models

class Condition(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class ReportSubmit(models.Model):

    # Animal type (Radio button)
    ANIMAL_TYPE_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('other', 'Other'),
    ]

    animal_type = models.CharField(
        max_length=10,
        choices=ANIMAL_TYPE_CHOICES
    )

    # Condition (Checkbox - multiple)
    conditions = models.ManyToManyField(
        Condition,
        blank=True
    )

    animal_count = models.PositiveIntegerField(default=1)

    # -------------------------
    # Location (Manual + Auto)
    # -------------------------
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

    LOCATION_SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
        ('mixed', 'Manual + Automatic'),
    ]

    location_source = models.CharField(
        max_length=10,
        choices=LOCATION_SOURCE_CHOICES,
        default='manual'
    )

    description = models.TextField(blank=True)

    # Auto date & time
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.animal_type} report at {self.manual_location}"

class ReportImage(models.Model):
    report = models.ForeignKey(
        ReportSubmit,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(upload_to="stray_photos/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for report {self.report.id}"

