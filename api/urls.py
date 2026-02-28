from django.urls import path, include
from rest_framework.routers import DefaultRouter
from donors.views import DonorViewSet
from requests.views import BloodRequestViewSet,MyRequestsViewSet
from dashboard.views import UserDashboardViewSet
from requests.views import initiate_payment,payment_history

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
]
