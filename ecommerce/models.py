from django.db import models
from django.contrib.auth.models import User

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
        """Calculate total completed payments"""
        return sum(payment.amount for payment in self.payments.filter(status='completed'))

    def get_outstanding_balance(self):
        """Calculate outstanding balance (total - paid)"""
        return self.get_total_amount() - self.get_total_paid()


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

    def __str__(self):
        return f"{self.amount} via {self.payment_method} for Order {self.order.id}"
class Debt(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='debts')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)

    def calculate_outstanding_balance(self):
        total_paid = sum(payment.amount for payment in self.order.payments.filter(status='completed')) # Sum of completed payments 

        total_order_amount = sum(item.price * item.quantity for item in self.order.items.all())  # sum of order items

        self.outstanding_balance = total_order_amount - total_paid # calculate outstanding balance

        self.is_paid = self.outstanding_balance <= 0 # mark debt as paid if balance is zero or less
        self.save() # save changes to the database

    def __str__(self):
        return f"Debt of {self.outstanding_balance} for {self.customer.user.username}"