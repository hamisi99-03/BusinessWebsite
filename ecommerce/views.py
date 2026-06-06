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
from django.utils import timezone
from decimal import Decimal

from .models import Customer, Product, Order, OrderItem, Payment, Debt, ProductImage, StockAdjustment, Category, Brand, Supplier, Consignment, ConsignmentItem, Expense
from .forms import OrderForm, PaymentForm, ProductForm, CustomUserCreationForm, CustomAuthenticationForm, ConsignmentForm, ConsignmentItemForm, ExpenseForm, SupplierForm

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
from django.shortcuts import render, redirect

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
    if request.user.is_staff:
        orders = Order.objects.select_related('customer__user').order_by('-order_date')
        customers = Customer.objects.select_related('user').all()
        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        delivered_orders = orders.filter(status='delivered').count()
        outstanding_total = sum(o.get_outstanding_balance() for o in orders)
        is_admin = True
    else:
        try:
            customer = Customer.objects.get(user=request.user)
            orders = Order.objects.filter(customer=customer).order_by('-order_date')
        except Customer.DoesNotExist:
            orders = []
        total_orders = orders.count()
        pending_orders = orders.filter(status='pending').count()
        delivered_orders = orders.filter(status='delivered').count()
        outstanding_total = sum(o.get_outstanding_balance() for o in orders)
        is_admin = False

    context = {
        'orders': orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'outstanding_total': outstanding_total,
        'is_admin': is_admin,
    }
    if request.user.is_staff:
        context['customers'] = customers

    return render(request, 'ecommerce/orders_list.html', context)


@login_required
def order_detail_view(request, pk):
    if request.user.is_staff:
        order = get_object_or_404(Order, pk=pk)
    else:
        try:
            customer = Customer.objects.get(user=request.user)
        except Customer.DoesNotExist:
            messages.error(request, 'Customer profile not found.')
            return redirect('dashboard')
        order = get_object_or_404(Order, pk=pk, customer=customer)
    # Attach total attribute to each order item for template use
    items = order.items.all()
    for item in items:
        item.total = item.price * item.quantity
    return render(request, 'ecommerce/order_detail.html', {'order': order})


@login_required
def debts_list_view(request):
    if request.user.is_staff:
        debts = Debt.objects.select_related('customer__user', 'order').order_by('-outstanding_balance')
        is_admin = True
    else:
        try:
            customer = Customer.objects.get(user=request.user)
            debts = Debt.objects.filter(customer=customer).select_related('order')
        except Customer.DoesNotExist:
            debts = []
        is_admin = False

    total_outstanding = sum(d.outstanding_balance for d in debts if not d.is_paid)
    paid_count = debts.filter(is_paid=True).count()

    for debt in debts:
        debt.amount_paid = debt.order.get_total_amount() - debt.outstanding_balance

    return render(request, 'ecommerce/debts_list.html', {
        'debts': debts,
        'total_outstanding': total_outstanding,
        'paid_count': paid_count,
        'is_admin': is_admin,
    })


@login_required
def profile_view(request):
    if request.method == 'POST':
        try:
            customer = request.user.customer
            if 'profile_picture' in request.FILES:
                customer.profile_picture = request.FILES['profile_picture']
                customer.save()
                messages.success(request, 'Profile picture updated.')
        except Customer.DoesNotExist:
            messages.error(request, 'Customer profile not found.')
        return redirect('profile_page')
    return render(request, 'ecommerce/profile.html', {'user': request.user})

@login_required
def change_password_view(request):
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib import messages
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile_page')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    return render(request, 'ecommerce/change_password.html', {'form': form})

@login_required
def order_product_view(request):
    product_id = request.GET.get('product_id')
    initial_product = None
    if product_id:
        initial_product = get_object_or_404(Product, pk=product_id)
        if initial_product.stock <= 0:
            messages.error(request, f"{initial_product.name} is out of stock.")
            return redirect('product_list')
    
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
        form = OrderForm(initial={'product': initial_product} if initial_product else None)

    return render(request, 'ecommerce/order_product.html', {'form': form, 'preselected_product': initial_product})

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

    total_collected = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    today = date.today()
    payments_this_month = Payment.objects.filter(
        payment_date__year=today.year,
        payment_date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0
    method_counts_raw = Payment.objects.values('payment_method').annotate(count=Count('id'))
    method_counts = {item['payment_method']: item['count'] for item in method_counts_raw}
    most_used_method = max(method_counts, key=method_counts.get) if method_counts else 'N/A'

    mpesa_count = payments.filter(payment_method='mpesa').count()
    cash_count = payments.filter(payment_method='cash').count()

    return render(request, 'ecommerce/payment_list.html', {
        'payments': payments,
        'total_collected': total_collected,
        'payments_this_month': payments_this_month,
        'method_counts': method_counts,
        'most_used_method': most_used_method,
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
    if request.method == 'POST':
        new_status = request.POST.get("status")
        order.status = new_status
        if new_status == 'delivered':
            order.shipped_date = timezone.now()
        order.save()
        
        # Update debt when order is delivered
        if new_status == 'delivered':
            try:
                debt = Debt.objects.get(order=order)
                debt.calculate_outstanding_balance()
            except Debt.DoesNotExist:
                pass
        
        messages.success(request, f"Order #{order.id} status updated to {new_status}.")
    return redirect("admin_dashboard")


@staff_member_required
def mark_payment_paid(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        # Create a payment record marking the order as fully paid
        amount = order.get_outstanding_balance()
        Payment.objects.create(
            order=order,
            amount=amount,
            payment_method='cash',
            status='completed'
        )
        
        # Update debt
        try:
            debt = Debt.objects.get(order=order)
            debt.calculate_outstanding_balance()
        except Debt.DoesNotExist:
            pass
        
        messages.success(request, f"Order #{order.id} marked as paid.")
    return redirect("admin_dashboard")


@staff_member_required  
def update_payment(request, pk):
    payment = get_object_or_404(Payment, id=pk)
    orders = Order.objects.all().order_by('-order_date')
    unpaid_orders = [o for o in orders if o.get_outstanding_balance() > 0]

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')

        if amount and payment_method:
            payment.amount = amount
            payment.payment_method = payment_method
            if payment_date:
                payment.payment_date = payment_date
            payment.save()
            # Update debt
            try:
                debt = Debt.objects.get(order=payment.order)
                debt.calculate_outstanding_balance()
            except Debt.DoesNotExist:
                pass
            messages.success(request, "Payment updated successfully.")
            return redirect('payment_list')

    return render(request, 'ecommerce/payment_form.html', {
        'order': payment.order,
        'orders': unpaid_orders,
        'payment': payment,
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
def add_payment_standalone(request):
    orders = Order.objects.all().order_by('-order_date')
    unpaid_orders = [o for o in orders if o.get_outstanding_balance() > 0]

    if request.method == 'POST':
        order_id = request.POST.get('order')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')

        if order_id and amount and payment_method:
            order = get_object_or_404(Order, id=order_id)
            Payment.objects.create(
                order=order,
                amount=Decimal(amount),
                payment_method=payment_method,
                payment_date=payment_date or timezone.now(),
                status='completed'
            )
            try:
                debt = Debt.objects.get(order=order)
                debt.calculate_outstanding_balance()
            except Debt.DoesNotExist:
                pass
            messages.success(
                request,
                f"Payment of KSh {amount} recorded successfully."
            )
            return redirect('payment_list')
        else:
            messages.error(request, "Please fill all required fields.")

    return render(request, 'ecommerce/payment_form.html', {
        'order': None,
        'orders': unpaid_orders,
        'payment': None,
    })


@staff_member_required
def add_payment(request, order_id=None):
    order = get_object_or_404(Order, id=order_id)
    orders = Order.objects.all().order_by('-order_date')
    # Only show orders with outstanding balance
    unpaid_orders = [o for o in orders if o.get_outstanding_balance() > 0]

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')

        if amount and payment_method:
            Payment.objects.create(
                order=order,
                amount=amount,
                payment_method=payment_method,
                payment_date=payment_date or timezone.now(),
                status='completed'
            )
            # Update debt
            try:
                debt = Debt.objects.get(order=order)
                debt.calculate_outstanding_balance()
            except Debt.DoesNotExist:
                pass
            messages.success(request, f"Payment of KSh {amount} recorded successfully.")
            return redirect('admin_dashboard')

    return render(request, 'ecommerce/payment_form.html', {
        'order': order,
        'orders': unpaid_orders,
        'payment': None,
    })


@staff_member_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            for image in request.FILES.getlist('images'):
                ProductImage.objects.create(product=product, image=image)
            messages.success(request, f"Product '{product.name}' added successfully.")
            return redirect("admin_products_list")
    else:
        form = ProductForm()

    return render(request, "ecommerce/product_form.html", {"form": form})


def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            for image in request.FILES.getlist('images'):
                ProductImage.objects.create(product=product, image=image)
            delete_ids = request.POST.getlist('delete_images')
            if delete_ids:
                ProductImage.objects.filter(id__in=delete_ids).delete()
            messages.success(request, f"Product '{product.name}' updated successfully.")
            return redirect("admin_products_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "ecommerce/product_form.html", {"form": form, "product": product})


@staff_member_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, f"Product '{product.name}' deleted successfully.")
        return redirect("admin_products_list")
    return render(request, "ecommerce/confirm_delete.html", {
        "product": product,
        "object_name": product.name,
        "cancel_url": '/admin-dashboard/products/'
    })


@staff_member_required
@require_POST
def adjust_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    adjustment_type = request.POST.get('adjustment_type')
    quantity = int(request.POST.get('quantity', 0))
    reason = request.POST.get('reason', '')

    if adjustment_type not in ('increase', 'decrease'):
        messages.error(request, 'Invalid adjustment type.')
        return redirect('admin_products_list')

    if quantity <= 0:
        messages.error(request, 'Quantity must be greater than zero.')
        return redirect('admin_products_list')

    if adjustment_type == 'increase':
        product.stock += quantity
    else:
        product.stock = max(0, product.stock - quantity)

    product.save()
    StockAdjustment.objects.create(
        product=product, adjusted_by=request.user,
        adjustment_type=adjustment_type, quantity=quantity, reason=reason
    )
    messages.success(request, f"Stock for '{product.name}' {adjustment_type}d by {quantity}.")
    return redirect('admin_products_list')


@staff_member_required
def admin_update_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == "POST":
        status = request.POST.get("status")
        # Validate that status is one of the allowed choices
        valid_statuses = [choice[0] for choice in Order._meta.get_field('status').choices]
        if status in valid_statuses:
            order.status = status
            order.save()
            messages.success(request, f"Order #{order.pk} status updated to {status}.")
            return redirect('orders_list')
        else:
            messages.error(request, "Invalid status selected.")
            return redirect('admin_update_order', pk=pk)
    
    # GET request
    status_choices = Order._meta.get_field('status').choices
    return render(request, 'ecommerce/admin_order_edit.html', {
        'order': order,
        'status_choices': status_choices
    })


@staff_member_required
def admin_delete_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == "POST":
        order.delete()
        messages.success(request, f"Order #{order.pk} deleted.")
        return redirect('orders_list')
    
    # GET request
    return render(request, 'ecommerce/confirm_delete.html', {
        'object': order,
        'object_name': f'Order #{order.pk}',
        'cancel_url': '/orders/list'
    })


def product_list(request):
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    
    products = Product.objects.all().prefetch_related('images')
    
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)
    
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    return render(request, "ecommerce/product_list.html", {
        "products": products,
        "categories": categories,
        "brands": brands,
        "selected_category": category_slug,
        "selected_brand": brand_slug,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'ecommerce/product_detail.html', {'product': product})


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


# -------------------
# Consignment Views
# -------------------
@staff_member_required
def consignment_list(request):
    consignments = Consignment.objects.all().prefetch_related('items__product')
    suppliers = Supplier.objects.all()
    return render(request, 'ecommerce/consignments.html', {'consignments': consignments, 'suppliers': suppliers})


@staff_member_required
def add_consignment(request):
    if request.method == 'POST':
        form = ConsignmentForm(request.POST)
        if form.is_valid():
            consignment = form.save()
            messages.success(request, f"Consignment {consignment.reference_number} created.")
            return redirect('consignment_list')
    else:
        form = ConsignmentForm()
    
    return render(request, 'ecommerce/consignment_form.html', {'form': form})


@staff_member_required
def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f"Supplier {supplier.name} added.")
            return redirect('consignment_list')
    else:
        form = SupplierForm()
    
    return render(request, 'ecommerce/supplier_form.html', {'form': form})


@staff_member_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.recorded_by = request.user
            expense.save()
            messages.success(request, f"Expense recorded: {expense.get_category_display()}")
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    
    return render(request, 'ecommerce/expense_form.html', {'form': form})


@staff_member_required
def expense_list(request):
    expenses = Expense.objects.all()
    return render(request, 'ecommerce/expenses.html', {'expenses': expenses})


# -------------------
# Financial Reports
# -------------------
@staff_member_required
def financial_report(request):
    from datetime import datetime, timedelta
    
    # Get date range from request or default to today
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
  
    today = date.today()
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        start = today
        end = today
    
    # Calculate metrics
    # Opening stock: stock before start_date (need historical tracking)
    # For now, use current stock minus recent receipts
    consignments = Consignment.objects.filter(date_received__range=[start, end])
    stock_received = sum(c.get_total_quantity() for c in consignments)
    
    # Purchases = cost from consignments in period
    total_purchases = sum(c.get_total_cost() for c in consignments)
    
    # Sales in period
    orders = Order.objects.filter(order_date__date__range=[start, end])
    total_sales = sum(o.get_total_amount() for o in orders)
    stock_sold = sum(sum(i.quantity for i in o.items.all()) for o in orders)
    
    # Expenses in period
    expenses = Expense.objects.filter(date__range=[start, end])
    total_expenses = sum(e.amount for e in expenses)
    
    # Current stock value (simplified - actual COGS needed)
    current_stock_value = sum(p.price * p.stock for p in Product.objects.all())
    
    # COGS (using average cost or from consignments - simplified)
    cogs = stock_sold * 0  # Will need unit cost tracking
    
    # Calculate average product cost from consignments
    total_units_received = sum(
        sum(item.quantity for item in c.items.all())
        for c in Consignment.objects.all()
    )
    total_cost_all = sum(c.get_total_cost() for c in Consignment.objects.all())
    avg_unit_cost = (total_cost_all / total_units_received) if total_units_received > 0 else 0
    cogs = stock_sold * avg_unit_cost
    
    gross_profit = total_sales - cogs
    net_profit = gross_profit - total_expenses
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(stock__lte=5, stock__gt=0)
    
    context = {
        'start_date': start,
        'end_date': end,
        'stock_received': stock_received,
        'stock_sold': stock_sold,
        'total_purchases': total_purchases,
        'total_sales': total_sales,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'low_stock_products': low_stock_products,
    }
    
    return render(request, 'ecommerce/financial_report.html', context)