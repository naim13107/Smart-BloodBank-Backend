from django.db import models
from django.conf import settings
from django.utils import timezone

class BloodRequest(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_requests'
    )
    
    donors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='donations_made', 
        blank=True
    )
    
    blood_group = models.CharField(max_length=3)
    bags_needed = models.PositiveIntegerField(default=1) 
    hospital_name = models.CharField(max_length=255, default="Unknown Hospital")
    donation_date = models.DateField(default=timezone.now)
    is_fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blood_group} for {self.recipient.email}"