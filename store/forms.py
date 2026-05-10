from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import GENRE_CHOICES


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name  = forms.CharField(max_length=50, required=False,
                                  widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')
        user.email      = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CheckoutForm(forms.Form):
    full_name   = forms.CharField(max_length=200,
                                   widget=forms.TextInput(attrs={'placeholder': 'Full name'}))
    address     = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Street address', 'rows': 3}))
    city        = forms.CharField(max_length=100,
                                   widget=forms.TextInput(attrs={'placeholder': 'City'}))
    postal_code = forms.CharField(max_length=20,
                                   widget=forms.TextInput(attrs={'placeholder': 'Postal / ZIP code'}))


class SubscribeForm(forms.Form):
    name  = forms.CharField(max_length=200, required=False,
                             widget=forms.TextInput(attrs={'placeholder': 'e.g. Priya Sharma'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    genre = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )