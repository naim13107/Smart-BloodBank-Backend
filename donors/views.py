from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
import datetime
from .models import DonorProfile
from .serializers import DonorProfileSerializer
from .permissions import Editpermission

class DonorViewSet(viewsets.ModelViewSet):
    
    queryset = DonorProfile.objects.all()
    serializer_class = DonorProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['blood_group','is_available'] 
    search_fields = ['user__address', 'blood_group'] 
    permission_classes = [Editpermission]

    def validate_future_date(self, date_str):
        if date_str:
            try:
                if isinstance(date_str, str):
                    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    date_obj = date_str
                
                if date_obj > timezone.now().date():
                    raise ValidationError({"last_donation_date": "The date cannot be in the future!"})
            except (ValueError, TypeError):
                pass

    def perform_create(self, serializer):
        self.validate_future_date(self.request.data.get('last_donation_date'))
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({
                "detail": "You have already created a donor profile."
            })

    def perform_update(self, serializer):
        self.validate_future_date(self.request.data.get('last_donation_date'))
        serializer.save()