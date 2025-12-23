from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Product, ProductImage, Order, OrderItem, Payment, Debt

# --- Customer ---
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address')
    search_fields = ('user__username',)

# --- Product Images Inline ---
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:80px;width:auto;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"

# --- Product ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "stock")
    search_fields = ("name",)
    list_filter = ("price",)
    inlines = [ProductImageInline] 

    def image_preview(self, obj):
        # Show first image preview if exists
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html('<img src="{}" style="max-height:200px;" />', first_image.image.url)
        return "No image uploaded"
    image_preview.short_description = "Current Image"

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
    inlines = [OrderItemInline, PaymentInline]

# --- Debt ---
@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'outstanding_balance', 'is_paid', 'paid_at')
    list_filter = ('is_paid',)
    search_fields = ('customer__user__username',)