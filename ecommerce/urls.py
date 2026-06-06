from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


from .views import (
    CustomerViewSet, ProductViewSet, OrderViewSet, OrderItemViewSet,
    PaymentViewSet, DebtViewSet, add_payment, add_payment_standalone, update_payment, delete_payment,
    register_view, login_view, logout_view,
    dashboard_view, orders_list_view, order_detail_view, debts_list_view,
    profile_view, ProfileView, order_product_view, change_password_view,
    custom_login, admin_dashboard, payment_list_view, update_order_status, add_product, update_product, delete_product, product_list, admin_products_list, reports_view,
    admin_update_order, admin_delete_order, adjust_stock, cart_view, add_to_cart, remove_from_cart, update_cart_item, checkout_from_cart,
    product_detail, mark_payment_paid,
    consignment_list, add_consignment, add_supplier, add_expense, expense_list, financial_report
)


router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'debts', DebtViewSet)

urlpatterns = [
    # Backwards-compat redirect: avoid DRF /api/debts/ intercepting template route
    path('debts/', lambda request: redirect('/api/my-debts/')),

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
    path('my-debts/', debts_list_view, name='debts_list'),
    path('profile-page/', profile_view, name='profile_page'),        # template profile
     path('auth/change-password/', change_password_view, name='change_password'),
    path('order-product/', order_product_view, name='order_product'),
    path('store/products/', product_list, name='product_list'),
     path('webcat/', product_list, name='webcat'),
     path('store/products/<int:pk>/', product_detail, name='product_detail'),

    # Cart
    path('cart/', cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/checkout/', checkout_from_cart, name='checkout_from_cart'),



    # Admin dashboard (protected by @staff_member_required)
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/reports/', reports_view, name='reports'),
    path('admin-dashboard/update-order/<int:pk>/', update_order_status, name='update_order_status'),
    path('admin-dashboard/orders/<int:pk>/mark-paid/', mark_payment_paid, name='mark_payment_paid'),
    path('admin-dashboard/orders/<int:pk>/update/', admin_update_order, name='admin_update_order'),
    path('admin-dashboard/orders/<int:pk>/delete/', admin_delete_order, name='admin_delete_order'),

    # Payments
    path('admin-dashboard/payments/add/',
         add_payment_standalone,
         name='add_payment_standalone'),
    path("admin-dashboard/orders/<int:order_id>/payments/add/", add_payment, name="add_payment"),
    path("admin-dashboard/payments/", payment_list_view, name="payment_list"),
    path("admin-dashboard/payments/<int:pk>/edit/", update_payment, name="edit_payment"),
    path("admin-dashboard/payments/<int:pk>/delete/", delete_payment, name="delete_payment"),



    # Products
    path("admin-dashboard/add-product/", add_product, name="add_product"),
    path("admin-dashboard/product/<int:pk>/edit/", update_product, name="update_product"),
    path("admin-dashboard/product/<int:pk>/delete/", delete_product, name="delete_product"),
    path("admin-dashboard/products/", admin_products_list, name="admin_products_list"),
    path("admin-dashboard/product/<int:pk>/adjust-stock/", adjust_stock, name="adjust_stock"),

    # Consignments & Expenses
    path("admin-dashboard/consignments/", consignment_list, name="consignment_list"),
    path("admin-dashboard/consignment/add/", add_consignment, name="add_consignment"),
    path("admin-dashboard/supplier/add/", add_supplier, name="add_supplier"),
    path("admin-dashboard/expenses/", expense_list, name="expense_list"),
    path("admin-dashboard/expense/add/", add_expense, name="add_expense"),
    path("admin-dashboard/financial-report/", financial_report, name="financial_report"),




    # browsable API login/logout
    path('api-auth/', include('rest_framework.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
