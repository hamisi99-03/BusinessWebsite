from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import (
    CustomerViewSet, ProductViewSet, OrderViewSet, OrderItemViewSet,
    PaymentViewSet, DebtViewSet,
    register_view, login_view, logout_view, dashboard_view,
    orders_list_view, order_detail_view, debts_list_view,
    profile_view, ProfileView  
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'debts', DebtViewSet)

urlpatterns = [
    # DRF router endpoints
    path('', include(router.urls)),

    #  Authentication endpoints
    path('auth/login/', obtain_auth_token, name='api_token_auth'),   # token login
    path('auth/register/', register_view, name='register'),          # function view
    path('auth/login-page/', login_view, name='login'),              # function view for page login
    path('auth/logout/', logout_view, name='logout'),                # logout
    path('auth/profile/', ProfileView.as_view(), name='profile'),    # APIView class

    #  Customer pages
    path('dashboard/', dashboard_view, name='dashboard'),
    path('orders/', orders_list_view, name='orders_list'),
    path('orders/<int:pk>/', order_detail_view, name='order_detail'),
    path('debts/', debts_list_view, name='debts_list'),
    path('profile-page/', profile_view, name='profile_page'),        # template profile

    # browsable API login/logout
    path('api-auth/', include('rest_framework.urls')),
]