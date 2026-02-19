from rest_framework import serializers
from .models import DonorProfile


class DonorProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = DonorProfile
        fields = ['id', 'user','full_name','age','email','blood_group', 'last_donation_date', 'is_available']
        read_only_fields = ['user', 'is_available'] 
  