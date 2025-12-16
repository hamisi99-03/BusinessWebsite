
from django import forms
from .models import Product, OrderItem

class OrderForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    quantity = forms.IntegerField(min_value=1)