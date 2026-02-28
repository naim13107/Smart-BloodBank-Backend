from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

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



class DonationTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tran_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, default='PENDING') # PENDING, SUCCESS, FAILED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.status}"
