from rest_framework import serializers
from .models import BloodRequest

class BloodRequestSerializer(serializers.ModelSerializer):
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    
    donor_emails = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='email',
        source='donors'
    )
    
    current_donors_count = serializers.IntegerField(source='donors.count', read_only=True)
    bags_still_needed = serializers.SerializerMethodField()

    class Meta:
        model = BloodRequest
        fields = [
            'id', 
            'recipient', 'recipient_email', 
            'donors', 'donor_emails', 
            'blood_group', 'bags_needed', 
            'current_donors_count', 'bags_still_needed',
            'hospital_name', 'donation_date','is_fulfilled', 'created_at'
        ]
        read_only_fields = ['recipient', 'donors', 'is_fulfilled']

    def get_bags_still_needed(self, obj):
        needed = obj.bags_needed - obj.donors.count()
        return max(0, needed)

    def validate_blood_group(self, value):
        valid_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
        if value not in valid_groups:
            raise serializers.ValidationError(f"{value} is not a valid blood group.")
        return value