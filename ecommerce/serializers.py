from rest_framework import serializers
from .models import Customer, Product, Order, OrderItem, Payment, Debt

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
    def get_total_amount(self, obj):
        return obj.get_total_amount()

    def get_total_paid(self, obj):
        return obj.get_total_paid()

    def get_outstanding_balance(self, obj):
        return obj.get_outstanding_balance()


class DebtSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    class Meta:
        model = Debt
        fields = '__all__'
        
class PaymentSerializer(serializers.ModelSerializer):
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'order', 'amount', 'payment_method', 'status', 'outstanding_balance']

    def get_outstanding_balance(self, obj):
        return obj.order.get_outstanding_balance()