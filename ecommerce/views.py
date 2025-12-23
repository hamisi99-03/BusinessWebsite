from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from .models import Customer, Product, Order, OrderItem, Payment, Debt, ProductImage
from .forms import OrderForm, PaymentForm, ProductForm, ProductImageFormSet
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
from django.shortcuts import render,redirect
from .forms import inlineformset_factory
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

    # Apply filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    return render(request, 'ecommerce/orders_list.html', {'orders': orders})
@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user.customer)
    return render(request, 'ecommerce/order_detail.html', {'order': order})

@login_required
def debts_list_view(request):
    debts = Debt.objects.filter(customer=request.user.customer)

    # Apply filter by paid/unpaid
    debt_status = request.GET.get('debt_status')
    if debt_status == 'paid':
        debts = debts.filter(is_paid=True)
    elif debt_status == 'unpaid':
        debts = debts.filter(is_paid=False)

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

            #  Check stock before creating anything
            if product.stock <= 0:
                messages.error(request, f"{product.name} is out of stock.")
                return redirect('orders_list')

            if quantity > product.stock:
                messages.error(request, f"Only {product.stock} items left in stock.")
                return redirect('orders_list')

            #  Only create order if stock is valid
            order = Order.objects.create(customer=request.user.customer, status='pending')

            # Add item
            order_item = OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
            order_item.save()  # ✅ ensures your custom save() runs

    

            # Confirmation message
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
    products = Product.objects.all()   # ✅ include products

    # Orders filter
    order_status = request.GET.get('order_status')
    if order_status:
        orders = orders.filter(status=order_status)

    # Debts filter
    debt_status = request.GET.get('debt_status')
    if debt_status == 'paid':
        debts = debts.filter(is_paid=True)
    elif debt_status == 'unpaid':
        debts = debts.filter(is_paid=False)

    # Payments filter
    payment_status = request.GET.get('payment_status')
    if payment_status:
        payments = payments.filter(status=payment_status)

    payment_date = request.GET.get('payment_date')
    if payment_date:
        payments = payments.filter(payment_date__date=payment_date)

    # Return products to template context
    return render(request, 'ecommerce/admin_dashboard.html', {
        'orders': orders,
        'debts': debts,
        'payments': payments,
        'products': products
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
def update_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    order = payment.order  # ✅ always fetch the related order

    if request.method == "POST":
        try:
            payment.amount = Decimal(request.POST.get("amount"))
            payment.status = request.POST.get("status")
            payment.save()   # triggers post_save signal
            messages.success(request, f"Payment #{payment.id} updated successfully.")
            return redirect("admin_dashboard")
        except Exception as e:
            messages.error(request, f"Error updating payment: {e}")
    else:
        # Render a template with order + payment details
        return render(request, "ecommerce/payment_form.html", {
            "form": PaymentForm(instance=payment),
            "payment": payment,
            "order": order
        })


@staff_member_required
def add_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.save()

            # Ensure debt exists and update it
            debt, created = Debt.objects.get_or_create(
                order=order,
                customer=order.customer,
                defaults={
                    "outstanding_balance": order.get_total_amount(),
                    "is_paid": False,
                    "paid_at": None,
                }
            )
            debt.calculate_outstanding_balance()

            messages.success(request, "Payment added successfully.")
            return redirect("admin_dashboard")
    else:
        form = PaymentForm()

    return render(request, "ecommerce/payment_form.html", {"form": form, "order": order})

@staff_member_required
def update_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    order = payment.order

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()

            debt = Debt.objects.filter(order=order).first()
            if debt:
                debt.calculate_outstanding_balance()

            messages.success(request, "Payment updated successfully.")
            return redirect("admin_dashboard")
    else:
        form = PaymentForm(instance=payment)

    return render(request, "ecommerce/payment_form.html", {"form": form, "order": order, "payment": payment})

@login_required
def payments_list_view(request):
    payments = Payment.objects.filter(order__customer=request.user.customer)

    # Apply filter by payment status
    payment_status = request.GET.get('payment_status')
    if payment_status:
        payments = payments.filter(status=payment_status)

    return render(request, 'ecommerce/payments_list.html', {'payments': payments})

@staff_member_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(request.POST, request.FILES, queryset=ProductImage.objects.none())
        if form.is_valid() and formset.is_valid():
            product = form.save()
            for f in formset.cleaned_data:
                if f and 'image' in f:
                    ProductImage.objects.create(product=product, image=f['image'])
            return redirect("admin_dashboard")
    else:
        form = ProductForm()
        formset = ProductImageFormSet(queryset=ProductImage.objects.none())
    return render(request, "ecommerce/product_form.html", {"form": form, "formset": formset})

ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    fields=('image',),
    extra=1,
    can_delete=True
)

def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    formset = ProductImageFormSet(request.POST or None, request.FILES or None, instance=product)

    if form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        return redirect("admin_dashboard")  # or your dashboard URL

    return render(request, "ecommerce/product_form.html", {
        "form": form,
        "formset": formset,
    })

@staff_member_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":  # confirm deletion
        product.delete()
        return redirect("admin_dashboard")
    return render(request, "ecommerce/confirm_delete.html", {"product": product})
def product_list(request):
    products = Product.objects.all()
    return render(request, "ecommerce/product_list.html", {"products": products})
@staff_member_required
def admin_products_list(request):
    products = Product.objects.all()
    return render(request, "ecommerce/admin_products_list.html", {"products": products})
