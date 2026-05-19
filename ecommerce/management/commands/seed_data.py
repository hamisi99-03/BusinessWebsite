from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ecommerce.models import Customer, Product, ProductImage, Order, OrderItem, Payment, Debt, StockAdjustment
from django.db import transaction
import sys

class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Check if data already exists (more than just admin)
            if User.objects.count() > 1:
                try:
                    answer = input("Database already has users. Continue? (yes/no): ")
                except EOFError:
                    answer = 'no'
                if answer.lower() != 'yes':
                    self.stdout.write(self.style.ERROR('Seeding cancelled.'))
                    return

            # Admin user
            admin, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@bizstore.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                admin.set_password('admin123')
                admin.save()
                self.stdout.write(self.style.SUCCESS('Created admin user'))
            else:
                self.stdout.write(self.style.WARNING('Admin user already exists'))

            # Regular customers
            customers_data = [
                {'username': 'alice', 'first_name': 'Alice', 'last_name': 'Wanjiru', 'email': 'alice@test.com'},
                {'username': 'bob', 'first_name': 'Bob', 'last_name': 'Otieno', 'email': 'bob@test.com'},
                {'username': 'carol', 'first_name': 'Carol', 'last_name': 'Muthoni', 'email': 'carol@test.com'},
                {'username': 'david', 'first_name': 'David', 'last_name': 'Kamau', 'email': 'david@test.com'},
                {'username': 'eve', 'first_name': 'Eve', 'last_name': 'Akinyi', 'email': 'eve@test.com'}
            ]

            customers = []
            for data in customers_data:
                user, created = User.objects.get_or_create(
                    username=data['username'],
                    defaults={
                        'email': data['email'],
                        'first_name': data['first_name'],
                        'last_name': data['last_name']
                    }
                )
                if created:
                    user.set_password('test1234')
                    user.save()
                # Create or get customer profile
                customer, _ = Customer.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone_number': self._get_phone_for_username(data['username']),
                        'address': self._get_address_for_username(data['username'])
                    }
                )
                customers.append(customer)

            # Products
            products_data = [
                {'name': 'Maize Flour 2kg', 'price': 180, 'stock': 50},
                {'name': 'Cooking Oil 1L', 'price': 250, 'stock': 30},
                {'name': 'Sugar 1kg', 'price': 120, 'stock': 45},
                {'name': 'Rice 2kg', 'price': 220, 'stock': 25},
                {'name': 'Bread Loaf', 'price': 60, 'stock': 20},
                {'name': 'Milk 500ml', 'price': 55, 'stock': 60},
                {'name': 'Bar Soap', 'price': 80, 'stock': 40},
                {'name': 'Washing Powder 1kg', 'price': 150, 'stock': 15}
            ]

            products = []
            for data in products_data:
                product, created = Product.objects.get_or_create(
                    name=data['name'],
                    defaults={
                        'price': data['price'],
                        'stock': data['stock']
                    }
                )
                products.append(product)

            # Orders and payments
            status_choices = ['pending', 'shipped', 'delivered', 'canceled']
            payment_methods = ['cash', 'mpesa', 'bank']

            orders_created = 0
            payments_created = 0
            debts_created = 0

            for i, customer in enumerate(customers):
                # Each customer gets 2-3 orders
                num_orders = 2 + (i % 2)  # alternates between 2 and 3
                for j in range(num_orders):
                    status = status_choices[j % len(status_choices)]
                    order = Order.objects.create(
                        customer=customer,
                        status=status
                    )
                    orders_created += 1

                    # Each order gets 1-2 order items
                    num_items = 1 + (j % 2)  # alternates between 1 and 2
                    for k in range(num_items):
                        product_index = (i + j + k) % len(products)
                        product = products[product_index]
                        quantity = 2  # fixed as per instructions
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.price
                        )

                    # Create payment for some orders (not all)
                    if (i + j) % 3 != 0:  # skip every third order
                        payment_method = payment_methods[(i + j) % len(payment_methods)]
                        amount = sum(item.price * item.quantity for item in order.items.all())
                        Payment.objects.create(
                            order=order,
                            amount=amount,
                            payment_method=payment_method,
                            status='completed',  # mark as completed for simplicity
                            created_by=admin
                        )
                        payments_created += 1

                    # Create debt for the order (if not fully paid)
                    debt, created = Debt.objects.get_or_create(
                        order=order,
                        customer=customer,
                        defaults={'outstanding_balance': 0}
                    )
                    if created:
                        debts_created += 1
                    # Calculate outstanding balance
                    debt.calculate_outstanding_balance()

            # Stock adjustments
            if len(products) >= 8:
                StockAdjustment.objects.create(
                    product=products[0],
                    adjusted_by=admin,
                    adjustment_type='increase',
                    quantity=20,
                    reason='Restock from supplier'
                )
                StockAdjustment.objects.create(
                    product=products[2],
                    adjusted_by=admin,
                    adjustment_type='decrease',
                    quantity=5,
                    reason='Damaged goods removed'
                )
                StockAdjustment.objects.create(
                    product=products[7],
                    adjusted_by=admin,
                    adjustment_type='increase',
                    quantity=10,
                    reason='Promotional stock added'
                )

            # Output summary
            self.stdout.write(self.style.SUCCESS('✅ Seed complete!'))
            self.stdout.write('─' * 40)
            self.stdout.write('ADMIN LOGIN')
            self.stdout.write('  Username: admin')
            self.stdout.write('  Password: admin123')
            self.stdout.write('─' * 40)
            self.stdout.write('CUSTOMER LOGINS (password for all: test1234)')
            self.stdout.write('  alice | bob | carol | david | eve')
            self.stdout.write('─' * 40)
            self.stdout.write(f'  Products created: {len(products)}')
            self.stdout.write(f'  Orders created:   {orders_created}')
            self.stdout.write(f'  Payments created: {payments_created}')
            self.stdout.write(f'  Debts created:    {debts_created}')

    def _get_phone_for_username(self, username):
        phones = {
            'alice': '0712345678',
            'bob': '0723456789',
            'carol': '0734567890',
            'david': '0745678901',
            'eve': '0756789012'
        }
        return phones.get(username, '0700000000')

    def _get_address_for_username(self, username):
        addresses = {
            'alice': 'Nairobi, Westlands',
            'bob': 'Mombasa Road, Nairobi',
            'carol': 'Kiambu Road, Nairobi',
            'david': 'Thika Road, Nairobi',
            'eve': 'Ngong Road, Nairobi'
        }
        return addresses.get(username, 'Nairobi')