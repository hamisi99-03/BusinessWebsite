from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number= models.CharField(max_length=20,blank =True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()

    def __str__(self):
        return self.name
    
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
        for payment in self.payments.filter(status__in=['completed'])
    )


    def get_outstanding_balance(self):
        """Calculate outstanding balance (total - paid)"""
        balance = self.get_total_amount() - self.get_total_paid()
        return max(balance, 0)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.id}"
    

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name='payments')
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[
        ('cash','Cash'),
        ('mpesa', 'M-pesa'),
    ], default='cash')
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')], default='pending')
    def clean(self):
        outstanding = self.order.get_outstanding_balance()
        if self.amount > outstanding:
            raise ValidationError(f"Payment exceeds outstanding balance ({outstanding}).")

    def save(self, *args, **kwargs):
        self.clean()  # run validation before saving
        super().save(*args, **kwargs)

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