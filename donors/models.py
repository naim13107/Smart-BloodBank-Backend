from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class DonorProfile(models.Model):
    BLOOD_GROUPS = [
        ('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='donor_profile'
    )
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    age = models.PositiveIntegerField()
    last_donation_date = models.DateField(null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.last_donation_date:
            self.is_available = True
        else:
            next_available_date = self.last_donation_date + timedelta(days=90)
            today = timezone.now().date()
            
            if today >= next_available_date:
                self.is_available = True
            else:
                self.is_available = False
        super().save(*args, **kwargs)