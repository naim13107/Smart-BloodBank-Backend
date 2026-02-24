from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from .models import BloodRequest
from .serializers import BloodRequestSerializer
from .permissions import IsRecipientOrAdmin
from rest_framework.exceptions import NotAuthenticated
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from api.pagination import DefaultPagination

class BloodRequestViewSet(viewsets.ModelViewSet):
    serializer_class = BloodRequestSerializer
    queryset = BloodRequest.objects.all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['blood_group']
    search_fields = ['hospital_name', 'blood_group']
    ordering_fields = ['created_at','donation_date','bags_needed'] 

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            if self.action == 'list':
                queryset = queryset.exclude(recipient=self.request.user)
                
        return queryset
    
    def get_permissions(self):
        if self.action in ['accept', 'withdraw']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsRecipientOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]
    
    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise NotAuthenticated("You must be logged in to create a blood request.")
        serializer.save(recipient=self.request.user)

    @action(detail=True, methods=['post','get'])
    def accept(self, request, pk=None):
        blood_request = self.get_object()
        user = request.user

        if timezone.now().date() > blood_request.donation_date:
            return Response(
                {"error": "This blood request has expired."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if not hasattr(user, 'donor_profile'):
            return Response(
                {"error": "You must create a donor profile before you can donate blood."},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = user.donor_profile
        
        if not profile.is_available:
            return Response(
                {"error": "You are currently ineligible to donate. Please check your dashboard for your next available date."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        if blood_request.donors.count() >= blood_request.bags_needed:
            return Response({"error": "This request is already fully covered."}, status=status.HTTP_400_BAD_REQUEST)
        
        if blood_request.donors.filter(id=user.id).exists():
            return Response({"error": "You have already accepted this request."}, status=status.HTTP_400_BAD_REQUEST)

        if blood_request.recipient == user:
            return Response({"error": "You cannot donate to your own request."}, status=status.HTTP_400_BAD_REQUEST)

        profile.is_available = False
        profile.last_donation_date = timezone.now().date()
        profile.save()

        blood_request.donors.add(user)

        if blood_request.donors.count() >= blood_request.bags_needed:
            blood_request.is_fulfilled = True
            blood_request.save()

        return Response({
            "status": "Success",
            "message": "Thank you! Your availability has been updated, and you are now a donor for this request."
        }, status=status.HTTP_200_OK)
    
    
    @action(detail=True, methods=['post','get'])
    def withdraw(self, request, pk=None):
        blood_request = self.get_object()
        user = request.user

       
        if not blood_request.donors.filter(id=user.id).exists():
            return Response(
                {"error": "You are not a registered donor for this request."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if timezone.now().date() >= blood_request.donation_date:
            return Response(
                {"error": "Withdrawal period has expired. You cannot withdraw on or after the donation date."}, 
                status=status.HTTP_403_FORBIDDEN
            )

   
        blood_request.donors.remove(user)

      
        if blood_request.donors.count() < blood_request.bags_needed:
            blood_request.is_fulfilled = False
            blood_request.save()

   
        if hasattr(user, 'donor_profile'):
            profile = user.donor_profile
            profile.is_available = True 
            profile.last_donation_date = None 
            profile.save()

        return Response({
            "status": "Success",
            "message": "You have successfully withdrawn. Your status is now 'Available' again."
        }, status=status.HTTP_200_OK)


class MyRequestsViewSet(viewsets.ModelViewSet):
    serializer_class = BloodRequestSerializer
    permission_classes = [IsAuthenticated] 
    pagination_class = DefaultPagination

    def get_queryset(self):
        return BloodRequest.objects.filter(recipient=self.request.user)
        
    def perform_create(self, serializer):
        serializer.save(recipient=self.request.user)