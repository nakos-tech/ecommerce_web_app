# xypher_lux/forms.py
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import CartItem, Order

class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    country_code = forms.CharField(max_length=5)  # Add this field
    phone_number = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # Password complexity check
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one digit.")
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

class SetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def clean(self):
        cleaned_password = super().clean()
        new_password = cleaned_password.get("new_password")
        confirm_password = cleaned_password.get("confirm_password")

        if new_password != confirm_password:
            raise ValidationError("Passwords do not mutch.")

        # Password complexity check
        if new_password and len(new_password) < 8:
            raiseValidationError("Password must be at least 8 characters long.")
        if new_password and not re.search("[A-Z]", new_password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if new_password and re.search("[a-z]", new_password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if new_password and not re.search("[0-9]", new_password):
            raise ValidationError("Password must contain at least one digit.")   \
        
        return cleaned_password

class AddToCartForm(forms.Form):
    # form for adding items to the cart 
    product_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            "class": "w-20 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
            "min": "1"
        })
    )
    size = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        })
    )
    color = forms.ChoiceField(
    required=False,
    widget=forms.Select(attrs={
        "class": "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
    })
)


    def __init__(self, *args, **kwargs):
        product = kwargs.pop("product", None)
        super().__init__(*args, **kwargs)

        if product:
            # Dynamically set size choices based on product sizes
            if prosduct.available_sizes:
                sizes = [(s.strip(), s.strip()) for s in product.available_sizes.split('')]
                self.fields['size'].choices = [('','Select Size')] + sizes

            if product.available_colors:
                colors = [(s.strip(), s.strip()) for c in product.available_colors.split(',')]
                self.fields['color'].choices = [('', 'Select Color')] + colors

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise ValidationError("Quantity must be at least 1.")
        return quantity


class UpdateCartItemForm(forms.ModelForm):
    # form for updating the items on the cart 
    class Meta:
        model = CartItem
        fields = ["quantity"]
        widgets = {
            "quantity": forms.NumberInput(attrs={
                "class": "w-20 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "min": "1"
            })
        }
    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")

        # check the stock availabilty 
        if hasattr(self.instance, "product"):
            if quantity > self.instance.product.stock:
                raise forms.ValidationError(
                    f"only {self.indtance.product.stock} items available"
                )
        return quantity
    
class CheckoutForm(forms.ModelForm):
    # form for checkout process

    class Meta:
        model = Order
        fields = [
            "shipping_address",
            "shipping_city",
            "shipping_country"
        ]

        widgets = {
            'shipping_address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Enter your street address'
            }),
            'shipping_city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'City'
            }),
            'shipping_country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Country'
            }),
            'shipping_postal_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Postal Code'
            })
        }

        labels = {
            "shipping_address": "street Address",
            "shipping_city": "City",
            "shipping_country": "Country",
        }



