import json
from django.db.models import Sum, Count
from datetime import date
from dateutil.relativedelta import relativedelta
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

from .models import Customer, Product, Order, OrderItem, Payment, Debt, ProductImage
from .forms import OrderForm, PaymentForm, ProductForm, ProductImageFormSet, CustomUserCreationForm, CustomAuthenticationForm
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

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    login(request, user)
                    messages.success(request, 'Account created successfully! Welcome.')
                    return redirect('dashboard')
            except IntegrityError:
                form.add_error(None, "A user with these details already exists.")
            except Exception as e:
                form.add_error(None, f"Registration failed: {str(e)}")
        else:
            form.add_error(None, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'You have been logged in successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))

@login_required
def dashboard_view(request):
    try:
        customer = Customer.objects.get(user=request.user)
        orders = Order.objects.filter(customer=customer).order_by('-order_date')

        total_orders = orders.count()
        total_spent = sum(o.get_total_amount() for o in orders)
        outstanding = sum(o.get_outstanding_balance() for o in orders)
        pending_orders = orders.filter(status='pending').count()
        recent_orders = orders[:5]

    except Customer.DoesNotExist:
        total_orders = 0
        total_spent = 0
        outstanding = 0
        pending_orders = 0
        recent_orders = []

    return render(request, 'ecommerce/dashboard.html', {
        'total_orders': total_orders,
        'total_spent': total_spent,
        'outstanding': outstanding,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
    })


@login_required
def orders_list_view(request):
    try:
        customer = Customer.objects.get(user=request.user)
        orders = Order.objects.filter(customer=customer).order_by('-order_date')

        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        delivered_orders = orders.filter(status='delivered').count()
        outstanding_total = sum(o.get_outstanding_balance() for o in orders)

    except Customer.DoesNotExist:
        orders = []
        total_orders = 0
        pending_orders = 0
        delivered_orders = 0
        outstanding_total = 0

    return render(request, 'ecommerce/orders_list.html', {
        'orders': orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
'outstanding_total': outstanding_total,
    })


@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user.customer)
    return render(request, 'ecommerce/order_detail.html', {'order': order})


@login_required
def debts_list_view(request):
    try:
        customer = Customer.objects.get(user=request.user)
        debts = Debt.objects.filter(customer=customer).select_related('order')
        total_outstanding = sum(d.outstanding_balance for d in debts if not d.is_paid)
        paid_count = debts.filter(is_paid=True).count()
    except Customer.DoesNotExist:
        debts = []
        total_outstanding = 0
        paid_count = 0

    return render(request, 'ecommerce/debts_list.html', {
        'debts': debts,
        'total_outstanding': total_outstanding,
        'paid_count': paid_count,
    })


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

            if product.stock <= 0:
                messages.error(request, f"{product.name} is out of stock.")
                return redirect('orders_list')

            if quantity > product.stock:
                messages.error(request, f"Only {product.stock} items left in stock.")
                return redirect('orders_list')

            order = Order.objects.create(customer=request.user.customer, status='pending')

            order_item = OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
            order_item.save()

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
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    outstanding_debt = Debt.objects.filter(is_paid=False).aggregate(total=Sum('outstanding_balance'))['total'] or 0
    unpaid_debt_count = Debt.objects.filter(is_paid=False).count()
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=5).order_by('stock')[:10]

    today = date.today()
    revenue_trend = []
    for i in range(5, -1, -1):
        month_date = today - relativedelta(months=i)
        result = Payment.objects.filter(
            payment_date__year=month_date.year,
            payment_date__month=month_date.month
        ).aggregate(total=Sum('amount'), count=Count('id'))
        revenue_trend.append({
            'month': month_date.strftime('%b %Y'),
            'total': result['total'] or 0,
            'count': result['count'] or 0,
        })

    recent_payments = Payment.objects.select_related('order__customer__user').order_by('-payment_date')[:8]
    top_debtors = Debt.objects.filter(is_paid=False).select_related('customer__user').order_by('-outstanding_balance')[:5]
    order_status_breakdown = list(Order.objects.values('status').annotate(count=Count('status')))

    status_choices = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    revenue_trend_json = json.dumps([{'month': d['month'], 'total': float(d['total']), 'count': d['count']} for d in revenue_trend])

    return render(request, 'ecommerce/admin_dashboard.html', {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'outstanding_debt': outstanding_debt,
        'unpaid_debt_count': unpaid_debt_count,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'revenue_trend': revenue_trend,
        'revenue_trend_json': revenue_trend_json,
        'recent_payments': recent_payments,
        'top_debtors': top_debtors,
        'order_status_breakdown': order_status_breakdown,
        'status_choices': status_choices,
    })


@staff_member_required
def reports_view(request):
    from datetime import datetime
    today = date.today()
    first_of_month = today.replace(day=1)
    
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    
    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else first_of_month
    except (ValueError, TypeError):
        date_from = first_of_month
    
    try:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else today
    except (ValueError, TypeError):
        date_to = today

    payments_in_range = Payment.objects.filter(
        payment_date__date__gte=date_from,
        payment_date__date__lte=date_to
    )
    total_collected = payments_in_range.aggregate(total=Sum('amount'))['total'] or 0
    payment_count = payments_in_range.count()
    avg_payment = (total_collected / payment_count) if payment_count > 0 else 0
    
    orders_in_range = Order.objects.filter(
        order_date__date__gte=date_from,
        order_date__date__lte=date_to
    )
    total_orders_period = orders_in_range.count()
    
    orders_by_status = list(orders_in_range.values('status').annotate(count=Count('status')))
    
    monthly_orders = []
    current_date = date_from.replace(day=1)
    end_date = date_to.replace(day=1)
    while current_date <= end_date:
        count = Order.objects.filter(
            order_date__year=current_date.year,
            order_date__month=current_date.month
        ).count()
        monthly_orders.append({
            'month': current_date.strftime('%b %Y'),
            'count': count,
        })
        month = current_date.month + 1
        year = current_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        current_date = current_date.replace(year=year, month=month)
    
    monthly_orders_json = json.dumps([{'month': d['month'], 'count': d['count']} for d in monthly_orders])
    
    return render(request, 'ecommerce/reports.html', {
        'date_from': date_from,
        'date_to': date_to,
        'total_collected': total_collected,
        'payment_count': payment_count,
        'avg_payment': avg_payment,
        'total_orders_period': total_orders_period,
        'orders_by_status': orders_by_status,
        'monthly_orders': monthly_orders,
        'monthly_orders_json': monthly_orders_json,
    })


@staff_member_required
def payment_list_view(request):
    payments = Payment.objects.all().order_by('-payment_date').select_related(
        'order', 'order__customer', 'order__customer__user'
    )

    total_collected = sum(p.amount for p in payments)
    mpesa_count = payments.filter(payment_method='mpesa').count()
    cash_count = payments.filter(payment_method='cash').count()

    return render(request, 'ecommerce/payment_list.html', {
        'payments': payments,
        'total_collected': total_collected,
        'mpesa_count': mpesa_count,
        'cash_count': cash_count,
    })


def custom_login(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'You have been logged in successfully.')
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, "auth/login.html", {"form": form})


@staff_member_required
@require_POST
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.status = request.POST.get("status")
    order.save()
    return redirect("admin_dashboard")


@staff_member_required
def update_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    order = payment.order

    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            # Note: we don't change created_by on update
            payment.save()
            messages.success(request, f"Payment #{payment.id} updated successfully.")
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentForm(instance=payment)

    # Get all orders for the dropdown
    orders = Order.objects.all().select_related('customer__user').order_by('-order_date')
    
    return render(request, "ecommerce/payment_form.html", {
        "form": form,
        "payment": payment,
        "order": order,
        "orders": orders,
    })


@staff_member_required
def delete_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == "POST":
        payment_id = payment.id
        payment.delete()
        messages.success(request, f"Payment #{payment_id} deleted successfully.")
        return redirect("payment_list")
    
    return render(request, "ecommerce/confirm_delete.html", {
        "payment": payment,
        "order": payment.order,
    })


@staff_member_required
def add_payment(request, order_id=None):
    if order_id:
        order = get_object_or_404(Order, pk=order_id)
    else:
        order = None

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()

            debt, _ = Debt.objects.get_or_create(
                order=payment.order,
                customer=payment.order.customer,
                defaults={
                    "outstanding_balance": payment.order.get_total_amount(),
                    "is_paid": False,
                    "paid_at": None,
                },
            )
            debt.calculate_outstanding_balance()

            messages.success(request, "Payment added successfully.")
            return redirect("admin_dashboard")

    else:
        form = PaymentForm()
        if order_id:
            # If we have an order_id from URL, we set the order in the form as initial and disable it
            form.fields['order'].initial = order
            form.fields['order'].widget.attrs['disabled'] = True

    # Get all orders for the dropdown
    orders = Order.objects.all().select_related('customer__user').order_by('-order_date')
    
    return render(request, "ecommerce/payment_form.html", {"form": form, "order": order, "orders": orders})


@staff_member_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        formset = ProductImageFormSet(
            request.POST, request.FILES, queryset=ProductImage.objects.none()
        )
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
        return redirect("admin_dashboard")

    return render(request, "ecommerce/product_form.html", {"form": form, "formset": formset})


@staff_member_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        return redirect("admin_dashboard")
    return render(request, "ecommerce/confirm_delete.html", {"product": product})


def product_list(request):
    products = Product.objects.all().prefetch_related('images')
    return render(request, "ecommerce/product_list.html", {"products": products})


@staff_member_required
def admin_products_list(request):
    products = Product.objects.all().prefetch_related('images')
    in_stock_count = products.filter(stock__gt=0).count()
    out_of_stock_count = products.filter(stock=0).count()
    total_value = sum(p.price * p.stock for p in products)

    return render(request, 'ecommerce/admin_products_list.html', {
        'products': products,
        'in_stock_count': in_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_value': total_value,
    })