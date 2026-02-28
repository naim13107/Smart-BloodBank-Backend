from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly,AllowAny
from .models import BloodRequest
from .serializers import BloodRequestSerializer
from .permissions import IsRecipientOrAdmin
from rest_framework.exceptions import NotAuthenticated
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from api.pagination import DefaultPagination
from rest_framework.decorators import api_view,permission_classes
from sslcommerz_lib import SSLCOMMERZ 
from donors.models import DonationTransaction 
from django.shortcuts import redirect
from django.conf import settings as main_settings
from django.http import HttpResponseRedirect


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
                {"error": "You must create a donor profile before you can donate blood , go to Dashboard and save you donor profile."},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = user.donor_profile
        
        # --- NEW CHECK: Verify Blood Group Match ---
        if profile.blood_group != blood_request.blood_group:
            return Response(
                {"error": f"Blood type mismatch. This request needs {blood_request.blood_group}, but you are registered as {profile.blood_group}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # -------------------------------------------
        
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
        profile.last_donation_date = blood_request.donation_date
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




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    amount = request.data.get('amount')
    user = request.user

    if not amount:
        return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    transaction = DonationTransaction.objects.create(
        user=user,
        amount=float(amount),
        status='PENDING'
    )

    settings = { 
        'store_id': 'bondh69a2b4734c5ba', 
        'store_pass': 'bondh69a2b4734c5ba@ssl', 
        'issandbox': True 
    }
    sslcz = SSLCOMMERZ(settings)
    
    post_body = {}
    post_body['total_amount'] = float(amount)
    post_body['currency'] = "BDT"
    post_body['tran_id'] = f"don_{transaction.id}" 
    post_body['success_url'] = f"{main_settings.BACKEND_URL}/api/v1/payment/success/"
    post_body['fail_url'] = f"{main_settings.BACKEND_URL}/api/v1/payment/fail/"
    post_body['cancel_url'] = f"{main_settings.BACKEND_URL}/api/v1/payment/cancel/"
    post_body['emi_option'] = 0
    post_body['cus_name'] = f"{user.first_name} {user.last_name}".strip() or "Donor"
    post_body['cus_email'] = user.email 
    post_body['cus_phone'] = getattr(user, 'phone_number', '01700000000') or '01700000000'
    post_body['cus_add1'] = getattr(user, 'address', 'Dhaka') or 'Dhaka'
    post_body['cus_city'] = "Dhaka"
    post_body['cus_country'] = "Bangladesh"
    post_body['shipping_method'] = "NO"
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Blood Donation"
    post_body['product_category'] = "Donation"
    post_body['product_profile'] = "general"

    response = sslcz.createSession(post_body)

    if response and response.get('status') == 'SUCCESS':
        return Response({'payment_url': response['GatewayPageURL']})
    
    return Response({
        "error": "Failed to create session", 
        "details": response
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_history(request):
    
    transactions = DonationTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    
    data = []
    for txn in transactions:
        data.append({
            "tran_id": str(txn.tran_id),
            "amount": str(txn.amount),
            "status": txn.status,
            "created_at": txn.created_at
        })
        
   
    return Response(data)


@api_view(['GET','POST'])
def payment_success(request):

    print("Inside success")

    tran_id = request.POST.get("tran_id") or request.GET.get("tran_id")

    print("TRAN_ID:", tran_id)

    if not tran_id:
        return HttpResponseRedirect(
            f"{main_settings.FRONTEND_URL}/dashboard/payment/success/"
        )

    donation_id = tran_id.split('_')[1]

    transaction = DonationTransaction.objects.get(id=donation_id)
    transaction.status = "SUCCESS"
    transaction.save()

    return HttpResponseRedirect(
        f"{main_settings.FRONTEND_URL}/dashboard/payment/success/"
    )

@api_view(['GET','POST'])
def payment_fail(request):

    tran_id = request.data.get("tran_id")
    donation_id = tran_id.split('_')[1]

    transaction = DonationTransaction.objects.get(id=donation_id)
    transaction.status = "FAILED"
    transaction.save()

    return HttpResponseRedirect(
        f"{main_settings.FRONTEND_URL}/dashboard/payment/fail/"
    )



@api_view(['GET','POST'])
def payment_cancel(request):

    return HttpResponseRedirect(
        f"{main_settings.FRONTEND_URL}/dashboard/payment/cancel/"
    )

