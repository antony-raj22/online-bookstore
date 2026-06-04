from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Book, GENRE_CHOICES, Order, Subscriber, UserProfile


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name  = forms.CharField(max_length=50, required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    mobile_number = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s-]{7,20}$',
                message='Enter a valid mobile number.',
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': '+91 98765 43210',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        }),
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'mobile_number', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')
        user.email      = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'mobile_number': self.cleaned_data['mobile_number'].strip()},
            )
        return user


class CheckoutForm(forms.Form):
    full_name   = forms.CharField(max_length=200,
                                   widget=forms.TextInput(attrs={'placeholder': 'Full name'}))
    address     = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Street address', 'rows': 3}))
    city        = forms.CharField(max_length=100,
                                   widget=forms.TextInput(attrs={'placeholder': 'City'}))
    postal_code = forms.CharField(max_length=20,
                                   widget=forms.TextInput(attrs={'placeholder': 'Postal / ZIP code'}))
    payment_method = forms.ChoiceField(
        choices=[
            ('razorpay', 'Razorpay'),
            ('cod', 'Cash on Delivery'),
        ],
        widget=forms.RadioSelect,
    )


class PaymentForm(forms.Form):
    card_name = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Name on card'}),
    )
    card_number = forms.CharField(
        max_length=19,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '4242 4242 4242 4242', 'inputmode': 'numeric'}),
    )
    expiry = forms.CharField(
        max_length=5,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'MM/YY'}),
    )
    cvv = forms.CharField(
        max_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'CVV', 'inputmode': 'numeric'}),
    )
    upi_id = forms.CharField(
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'name@bank'}),
    )


class TrackingForm(forms.Form):
    order_id = forms.IntegerField(widget=forms.NumberInput(attrs={'placeholder': 'Order number'}))
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Postal / ZIP code'}),
    )


class AdminBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'price', 'cover_url', 'stock', 'genre']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
        }


class AdminOrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'payment_status']


class CancelOrderForm(forms.Form):
    reason = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'placeholder': 'Tell us why you want to cancel this order',
            'rows': 3,
        }),
    )


class SubscribeForm(forms.Form):
    name  = forms.CharField(max_length=200, required=False,
                             widget=forms.TextInput(attrs={'placeholder': 'e.g. Priya Sharma'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    mobile_number = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9\s-]{7,20}$',
                message='Enter a valid mobile number.',
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': '+91 98765 43210',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        }),
    )
    plan = forms.ChoiceField(
        choices=[
            ('monthly', '1 Month - Rs.100'),
            ('quarterly', '3 Months - Rs.250'),
            ('yearly', 'Yearly - Rs.900'),
        ],
        widget=forms.RadioSelect,
        initial='monthly',
    )
    genre = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
