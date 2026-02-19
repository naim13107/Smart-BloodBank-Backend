from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from donors.models import DonorProfile
from requests.models import BloodRequest
from donors.serializers import DonorProfileSerializer
from requests.serializers import BloodRequestSerializer

class UserDashboardViewSet(viewsets.ViewSet):
    """
    For the logged-in user.

    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        user = request.user
        
        # 1. User Details
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "date_joined": user.date_joined.strftime('%Y-%m-%d'),
        }

        # 2. Donor Profile Details
        profile = DonorProfile.objects.filter(user=user).first()
        profile_data = DonorProfileSerializer(profile).data if profile else "No donor profile found."

        # 3. Define the precise "Donation Date" boundary 
        # (Using today's date as the strict point of no return)
        today = timezone.now().date()

        # ---------------------------------------------------------
        # ACTIVE DASHBOARD (Happening today or in the future)
        # ---------------------------------------------------------
        # Requests I made for today or the future
        active_requests = BloodRequest.objects.filter(
            recipient=user, 
            donation_date__gte=today
        )
        
        # Requests I accepted for today or the future
        active_commitments = BloodRequest.objects.filter(
            donors=user, 
            donation_date__gte=today
        )

        # ---------------------------------------------------------
        # HISTORY (Passed the donation date, strictly in the past)
        # ---------------------------------------------------------
        # Donated: Requests I accepted where the donation date has passed
        donated_history = BloodRequest.objects.filter(
            donors=user, 
            donation_date__lt=today
        )

        # Received: Requests I made where the date passed AND at least one person donated
        received_history = BloodRequest.objects.filter(
            recipient=user, 
            donation_date__lt=today, 
            donors__isnull=False
        ).distinct() # .distinct() prevents duplicates if multiple donors joined

        # Canceled: Requests I made where the date passed, but NOBODY showed up to donate
        canceled_history = BloodRequest.objects.filter(
            recipient=user, 
            donation_date__lt=today, 
            donors__isnull=True
        )

        return Response({
            "user_details": user_info,
            "donor_profile": profile_data,
            "active_dashboard": {
                "ongoing_requests": BloodRequestSerializer(active_requests, many=True).data,
                "upcoming_donations": BloodRequestSerializer(active_commitments, many=True).data,
            },
            "history": {
                "received": BloodRequestSerializer(received_history, many=True).data,
                "donated": BloodRequestSerializer(donated_history, many=True).data,
                "canceled": BloodRequestSerializer(canceled_history, many=True).data,
            },
            "summary_stats": {
                "total_completed_donations": donated_history.count(),
                "total_received_requests": received_history.count(),
                "is_available": profile.is_available if profile else False
            }
        }, status=status.HTTP_200_OK)