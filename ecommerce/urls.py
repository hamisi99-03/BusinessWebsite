from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    CustomerViewSet, ProductViewSet, OrderViewSet, OrderItemViewSet,
    PaymentViewSet, DebtViewSet, add_payment, add_payment, update_payment,
    register_view, login_view, logout_view,
    dashboard_view, orders_list_view, order_detail_view, debts_list_view,
    profile_view, ProfileView, order_product_view,
    custom_login, admin_dashboard, update_order_status, update_payment,add_product, update_product, delete_product, product_list, admin_products_list  #  use custom_login + admin_dashboard
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

    # Authentication endpoints
    path('auth/login/', obtain_auth_token, name='api_token_auth'),   # token login
    path('auth/register/', register_view, name='register'),          # function view
    path('auth/login-page/', custom_login, name='login'),            # custom login with redirect logic
    path('auth/logout/', logout_view, name='logout'),                # logout
    path('auth/profile/', ProfileView.as_view(), name='profile'),    # APIView class

    # Customer pages
    path('dashboard/', dashboard_view, name='dashboard'),
    path('orders/list', orders_list_view, name='orders_list'),
    path('orders/detail/<int:pk>/', order_detail_view, name='order_detail'),
    path('debts/', debts_list_view, name='debts_list'),
    path('profile-page/', profile_view, name='profile_page'),        # template profile
    path('order-product/', order_product_view, name='order_product'),
    path('products/', product_list, name='product_list'),

    # Admin dashboard (protected by @staff_member_required)
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/update-order/<int:pk>/', update_order_status, name='update_order_status'),

    # Payments
    path("admin-dashboard/orders/<int:order_id>/payments/add/", add_payment, name="add_payment"),
    path("admin-dashboard/payments/<int:pk>/edit/", update_payment, name="edit_payment"),

    # Products
    path("admin-dashboard/add-product/", add_product, name="add_product"),
    path("admin-dashboard/product/<int:pk>/edit/", update_product, name="update_product"),
    path("admin-dashboard/product/<int:pk>/delete/", delete_product, name="delete_product"),
    path("admin-dashboard/products/", admin_products_list, name="admin_products_list"),




    # browsable API login/logout
    path('api-auth/', include('rest_framework.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
