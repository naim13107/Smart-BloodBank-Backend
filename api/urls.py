from django.urls import path, include
from rest_framework.routers import DefaultRouter
from donors.views import DonorViewSet
from blood_request.views import BloodRequestViewSet,MyRequestsViewSet
from dashboard.views import UserDashboardViewSet
from blood_request.views import initiate_payment,payment_history,payment_success,payment_cancel,payment_fail

router = DefaultRouter()
router.register('donors', DonorViewSet, basename='donors')
router.register('requests', BloodRequestViewSet, basename='requests')
router.register('dashboard', UserDashboardViewSet, basename='dashboard')
router.register('my-requests', MyRequestsViewSet, basename='my-requests')



urlpatterns = [
  
    path('', include(router.urls)),
  
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path("payment/initiate/",initiate_payment,name='initiate-payment'),
    path('payment/history/',payment_history, name='payment_history'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/fail/', payment_fail, name='payment_fail'),
    path('payment/cancel/', payment_cancel, name='payment_cancel'),


]
