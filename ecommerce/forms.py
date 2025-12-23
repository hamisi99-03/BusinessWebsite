from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.forms.widgets import ClearableFileInput
from .models import Product, OrderItem, Payment, ProductImage


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
        fields = ['order', 'amount', 'payment_method']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "price", "stock"]


# Custom widget to separate preview and file input
class CustomImageWidget(ClearableFileInput):
    template_name = "widgets/custom_image_widget.html"


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image"]
        widgets = {"image": CustomImageWidget}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow empty when deleting, so DELETE checkbox works
        self.fields["image"].required = False


#  Custom formset enforcing at least one image
class ProductImageBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if form.cleaned_data.get("image"):
                count += 1
        if count == 0:
            raise forms.ValidationError("Each product must have at least one image.")


#  Inline formset linking Product → ProductImage
ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,          # use custom form with widget
    formset=ProductImageBaseFormSet,  # use custom formset with validation
    extra=0,
    can_delete=True
)