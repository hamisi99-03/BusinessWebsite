from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number= models.CharField(max_length=20,blank =True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')


    def __str__(self):
        return self.name
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def delete(self, *args, **kwargs):
        self.image.delete(save=False)  # delete the file from disk
        super().delete(*args, **kwargs)


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled')], default='pending')

    def __str__(self):
        return f"Order {self.id} by {self.customer.user.username}"
    
    def get_total_amount(self):
        """Calculate total order amount from items"""
        return sum(item.price * item.quantity for item in self.items.all())

    def get_total_paid(self):
        """Calculate total completed + pending payments"""
        return sum(
            payment.amount
            for payment in self.payments.filter(status__in=['completed', 'pending'])
        )

    def get_outstanding_balance(self):
        """Calculate outstanding balance (total - paid)"""
        balance = self.get_total_amount() - self.get_total_paid()
        return max(balance, 0)

from django.core.exceptions import ValidationError

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"

    def clean(self):
        #  Prevent ordering more than available stock
        if self.pk:
            # If updating, include old quantity back before validation
            old_quantity = OrderItem.objects.get(pk=self.pk).quantity
            available_stock = self.product.stock + old_quantity
        else:
            available_stock = self.product.stock

        if self.quantity > available_stock:
            raise ValidationError(f"Only {available_stock} items left in stock.")

    def save(self, *args, **kwargs):
        # Run validation first
        if self.pk:
            # If updating, restore old quantity before checking
            old_quantity = OrderItem.objects.get(pk=self.pk).quantity
            available_stock = self.product.stock + old_quantity
        else:
            available_stock = self.product.stock

        if self.quantity > available_stock:
            raise ValidationError(f"Only {available_stock} items left in stock.")

        super().save(*args, **kwargs)

        # Subtract new quantity safely
        if self.pk:
            # If updating, restore old quantity before subtracting
            old_quantity = OrderItem.objects.get(pk=self.pk).quantity
            self.product.stock += old_quantity

        self.product.stock -= self.quantity
        if self.product.stock < 0:
            self.product.stock = 0  # safeguard
        self.product.save()

    def delete(self, *args, **kwargs):
        #  Restore stock when item is removed
        self.product.stock += self.quantity
        self.product.save()
        super().delete(*args, **kwargs)


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50,
        choices=[('cash','Cash'), ('mpesa', 'M-pesa'), ('bank', 'Bank Transfer')],
        default='cash'
    )
    status = models.CharField(
        max_length=50,
        choices=[('pending', 'Pending'), ('completed', 'Completed')],
        default='pending'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_created')

    def clean(self):
        # Exclude current payment when editing
        total_paid_excluding_current = sum(
            p.amount for p in self.order.payments.exclude(pk=self.pk)
        )
        new_total_paid = total_paid_excluding_current + self.amount

        if new_total_paid > self.order.get_total_amount():
            raise ValidationError(
                f"Payment exceeds order total ({self.order.get_total_amount()}). "
                f"Max allowed is {self.order.get_total_amount() - total_paid_excluding_current}."
            )

    def save(self, *args, **kwargs):
        self.clean()  # run validation before saving
        super().save(*args, **kwargs)
        total_paid = sum(p.amount for p in self.order.payments.all())
        if total_paid >= self.order.get_total_amount():
            # fully paid → mark all as completed
            self.order.payments.update(status='completed')
        else:
            # still balance → mark all as pending
            self.order.payments.update(status='pending')

    def __str__(self):
        return f"{self.amount} via {self.payment_method} for Order {self.order.id}"

class Debt(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='debts')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def calculate_outstanding_balance(self):
        # Sum of payments (only completed ones should reduce debt)
        total_paid = sum(
            payment.amount for payment in self.order.payments.filter(status='completed')
        )

        # Total order amount = sum of items
        total_order_amount = sum(
            item.price * item.quantity for item in self.order.items.all()
        )

        # Clamp balance at zero
        balance = total_order_amount - total_paid
        self.outstanding_balance = max(balance, 0)

        # Mark debt as paid if balance is zero
        if self.outstanding_balance == 0:
            if not self.is_paid:
                self.is_paid = True
                if not self.paid_at:
                    from django.utils import timezone
                    self.paid_at = timezone.now().date()
        else:
            self.is_paid = False
            self.paid_at = None

        self.save()
    def __str__(self):
        return f"Debt of {self.outstanding_balance} for {self.customer.user.username}"


class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = [('increase', 'Increase'), ('decrease', 'Decrease')]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_adjustments')
    adjusted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    quantity = models.PositiveIntegerField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.adjustment_type} {self.quantity} for {self.product.name}"


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Consignment(models.Model):
    reference_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    date_received = models.DateField()
    freight_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customs_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date_received']

    def __str__(self):
        return f"Consignment {self.reference_number}"

    def get_total_cost(self):
        return sum(item.total_cost for item in self.items.all())

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class ConsignmentItem(models.Model):
    consignment = models.ForeignKey(Consignment, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    units_per_box = models.PositiveIntegerField(default=1)
    cost_per_box = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_cost(self):
        if self.units_per_box > 0:
            boxes = self.quantity // self.units_per_box
            remaining_units = self.quantity % self.units_per_box
            return boxes * self.cost_per_box + remaining_units * self.cost_per_unit
        return self.quantity * self.cost_per_unit


EXPENSE_CATEGORIES = [
    ('transport', 'Transport'),
    ('salaries', 'Salaries'),
    ('rent', 'Rent'),
    ('utilities', 'Utilities'),
    ('marketing', 'Marketing'),
    ('supplies', 'Supplies'),
    ('other', 'Other'),
]


class Expense(models.Model):
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)
    description = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_category_display()}: KSh {self.amount}"
    


class Cart(models.Model):
    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def get_item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f"Cart of {self.customer.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    

