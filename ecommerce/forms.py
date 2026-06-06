from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Product, OrderItem, Payment, Customer, Consignment, ConsignmentItem, Expense, Supplier, ProductImage

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'})
    )
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John'})
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doe'})
    )
    phone_number = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254 700 000 000'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your address'})
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'})
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat your password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            customer = user.customer
            customer.phone_number = self.cleaned_data.get("phone_number", "")
            customer.address = self.cleaned_data.get("address", "")
            customer.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )


class ProductChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="height:40px;width:auto;"> {obj.name}'
        return obj.name


class OrderForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'payment_method', 'notes']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "stock", "category", "brand"]
        widgets = {
            "name": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g Samsung Galaxy S22'}),
            "description": forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the product'}),
            "price": forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            "stock": forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'min': '0'}),
            "category": forms.Select(attrs={'class': 'form-select'}),
            "brand": forms.Select(attrs={'class': 'form-select'}),
        }


class ConsignmentForm(forms.ModelForm):
    class Meta:
        model = Consignment
        fields = ['reference_number', 'supplier', 'date_received', 'freight_cost', 'customs_tax', 'other_expenses']
        widgets = {
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g CON-2024-001'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'date_received': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'freight_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'customs_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'other_expenses': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class ConsignmentItemForm(forms.ModelForm):
    class Meta:
        model = ConsignmentItem
        fields = ['product', 'quantity', 'units_per_box', 'cost_per_box', 'cost_per_unit']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'units_per_box': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'cost_per_box': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'cost_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'description', 'amount', 'date']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact person'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254 700 000 000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}),
        }


ProductImageFormSet = forms.inlineformset_factory(
    Product, ProductImage,
    fields=['image'],
    extra=5,
    widgets={'image': forms.ClearableFileInput(attrs={'class': 'form-control'})}
)