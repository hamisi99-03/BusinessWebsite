from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . views import (
    CustomerViewSet, ProductViewSet, OrderViewSet,OrderItemViewSet,
    PaymentViewSet, DebtViewSet
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'debts', DebtViewSet)
urlpatterns = [
    path('', include(router.urls)),
]