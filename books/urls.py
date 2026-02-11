from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BusinessViewSet, CashbookViewSet, MemberViewSet, 
    CategoryViewSet, PartyViewSet, PaymentModeViewSet, 
    TransactionViewSet, SummaryView
)
from .report_views import ReportsViewSet

router = DefaultRouter()
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'cashbooks', CashbookViewSet, basename='cashbook')
router.register(r'members', MemberViewSet, basename='member')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'parties', PartyViewSet, basename='party')
router.register(r'payment-modes', PaymentModeViewSet, basename='payment-mode')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'reports', ReportsViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
    path('summary/', SummaryView.as_view(), name='summary'),
]
