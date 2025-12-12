from django.contrib import admin
from .models import Payment
from .models import Customer, Product, Order, OrderItem, Payment, Debt

admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
#admin.site.register(Payment)
#admin.site.register(Debt)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'status', 'outstanding_balance')

    def outstanding_balance(self, obj):
        return obj.order.get_outstanding_balance()
    outstanding_balance.short_description = "Needs Paid"

@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ('order', 'customer', 'outstanding_balance', 'is_paid', 'paid_at')