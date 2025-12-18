from django.contrib import admin
from .models import Customer, Product, Order, OrderItem, Payment, Debt

# --- Customer ---
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address')
    search_fields = ('user__username',)

# --- Product ---
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "stock")
    search_fields = ("name",)
    list_filter = ("price",)

# --- Inline definitions ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

# --- Order ---
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer', 'order_date', 'status',
        'get_total_amount', 'get_total_paid', 'get_outstanding_balance'
    )
    list_filter = ('status', 'order_date')
    search_fields = ('customer__user__username',)
    inlines = [OrderItemInline, PaymentInline]   # 👈 Items + Payments editable inline

# --- Debt ---
@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'outstanding_balance', 'is_paid', 'paid_at')
    list_filter = ('is_paid',)
    search_fields = ('customer__user__username',)