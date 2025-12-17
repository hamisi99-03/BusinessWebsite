from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from .models import Customer, Product, Order, OrderItem, Payment, Debt
from .forms import OrderForm, PaymentForm
from .serializers import (
    CustomerSerializer, ProductSerializer, OrderSerializer,
    OrderItemSerializer, PaymentSerializer, DebtSerializer
)
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.exceptions import ValidationError

from decimal import Decimal

# -------------------
# DRF ViewSets
# -------------------
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

# -------------------
# Auth Views
# -------------------
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    # Customer auto-created by signal, so no manual creation here
                    login(request, user)
                    return redirect('dashboard')
            except IntegrityError:
                # Handles duplicate username/email or DB constraint errors
                form.add_error(None, "A user with these details already exists.")
            except Exception as e:
                # Catch-all for unexpected errors
                form.add_error(None, f"Registration failed: {str(e)}")
        else:
            # Form validation errors (password too weak, username invalid, etc.)
            form.add_error(None, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, 'auth/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))

# -------------------
# Customer Pages
# -------------------
@login_required
def dashboard_view(request):
    orders = Order.objects.filter(customer=request.user.customer)
    debts = Debt.objects.filter(customer=request.user.customer)
    payments = Payment.objects.filter(order__customer=request.user.customer)
    return render(request, 'ecommerce/dashboard.html', {
        'orders': orders,
        'debts': debts,
        'payments': payments
    })

@login_required
def orders_list_view(request):
    orders = Order.objects.filter(customer=request.user.customer)
    return render(request, 'ecommerce/orders_list.html', {'orders': orders})

@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user.customer)
    return render(request, 'ecommerce/order_detail.html', {'order': order})

@login_required
def debts_list_view(request):
    debts = Debt.objects.filter(customer=request.user.customer)
    return render(request, 'ecommerce/debts_list.html', {'debts': debts})

@login_required
def profile_view(request):
    return render(request, 'ecommerce/profile.html', {'user': request.user})
@login_required
def order_product_view(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']

            # Create order
            order = Order.objects.create(customer=request.user.customer, status='pending')

            # Add item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

            #  Confirmation message
            messages.success(request, f"Order #{order.id} placed successfully for {product.name}!")

            return redirect('orders_list')
    else:
        form = OrderForm()

    return render(request, 'ecommerce/order_product.html', {'form': form})

# -------------------
# API Profile Endpoint
# -------------------
User = get_user_model()

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "date_of_birth": getattr(user, "date_of_birth", None),
            "profile_photo": getattr(user, "profile_photo", None),
        }
        return Response(data)
    



@staff_member_required
def admin_dashboard(request):
    orders = Order.objects.all()
    debts = Debt.objects.all()
    payments = Payment.objects.all()
    return render(request, 'ecommerce/admin_dashboard.html', {
        'orders': orders,
        'debts': debts,
        'payments': payments
    })
def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            #  Redirect based on role
            if user.is_staff:   # admin user
                return redirect('admin_dashboard')
            else:               # customer user
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})
@staff_member_required
@require_POST
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.status = request.POST.get("status")
    order.save()
    return redirect("admin_dashboard")

from decimal import Decimal

@staff_member_required
@require_POST
def update_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    try:
        payment.amount = Decimal(request.POST.get("amount"))
        payment.status = request.POST.get("status")
        payment.save()   # 👈 triggers post_save signal
        messages.success(request, f"Payment #{payment.id} updated successfully.")
    except Exception as e:
        messages.error(request, f"Error updating payment: {e}")
    return redirect("admin_dashboard")


@staff_member_required
def add_or_update_payment(request, pk=None):
    if pk:
        payment = get_object_or_404(Payment, pk=pk)
    else:
        payment = None

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Payment saved successfully.")
                return redirect("admin_dashboard")
            except ValidationError as e:
                # 👇 show friendly error message
                messages.error(request, f"Error: {e.message}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentForm(instance=payment)

    return render(request, "ecommerce/payment_form.html", {"form": form})
