

from rest_framework import viewsets
from .models import Customer, Product, Order, OrderItem, Payment, Debt
from .serializers import (
    CustomerSerializer, ProductSerializer, OrderSerializer,
    OrderItemSerializer, PaymentSerializer, DebtSerializer
)

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class DebtViewSet(viewsets.ModelViewSet):
    queryset = Debt.objects.all()
    serializer_class = DebtSerializer
