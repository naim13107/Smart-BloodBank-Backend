from rest_framework import serializers

class DashboardSummarySerializer(serializers.Serializer):
    """
    A non-model serializer to represent the dashboard structure.
    """
    user_details = serializers.DictField()
    donor_profile = serializers.DictField()
    requests = serializers.ListField()
    donations = serializers.ListField()
    cancellations = serializers.ListField()