
from django import forms
from .models import Product, OrderItem,Payment, ProductImage
from django.forms import modelformset_factory
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
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control'}))


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'payment_method']
        
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "stock"]
ProductImageFormSet = modelformset_factory(
    ProductImage,
    fields=('image',),
    extra=1,  
    
)
