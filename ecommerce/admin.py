from django.contrib import admin
from django.utils.html import format_html
from .models import Customer, Product, ProductImage, Order, OrderItem, Payment, Debt, Category, Brand, Supplier, Consignment, ConsignmentItem, Expense

# --- Category & Brand ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}

# --- Supplier ---
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone')
    search_fields = ('name', 'contact_person')

# --- Consignment ---
class ConsignmentItemInline(admin.TabularInline):
    model = ConsignmentItem
    extra = 1
    autocomplete_fields = ['product']

@admin.register(Consignment)
class ConsignmentAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'supplier', 'date_received', 'get_total_quantity', 'get_total_cost')
    list_filter = ('date_received', 'supplier')
    search_fields = ('reference_number',)
    inlines = [ConsignmentItemInline]
    date_hierarchy = 'date_received'

# --- Expense ---
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'date', 'recorded_by')
    list_filter = ('category', 'date')
    search_fields = ('description',)

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
    list_display = ("id", "name", "category", "brand", "price", "stock")
    search_fields = ("name", "category__name", "brand__name")
    list_filter = ("category", "brand", "price")
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