# myapp/forms.py
from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class SyncForm(forms.Form):
    credentials_placeholder = "Source@Account Password Destination@Account Password\ntest@email.com Password123 test@email.com Password123"
    source = forms.CharField(
        label="source",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "mail.source.tld"}
        ),
    )
    destination = forms.CharField(
        label="destination",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "sv.destination.tld"}
        ),
    )
    input_text = forms.CharField(
        label="input_text",
        widget=forms.Textarea(
            attrs={
                "class": "form-control w-75 mx-auto",
                "rows": 5,
                "autocomplete": "off",
                "placeholder": credentials_placeholder,
            }
        ),
    )
    additional_arguments = forms.CharField(
        label="additional_arguments",
        required=False,
        initial="",
        widget=forms.TextInput(
            attrs={
                "class": "form-control d-inline-flex",
                "style": "max-width: 300px;",
                "placeholder": "--nossl1 --timeout 300 --office2  .....",
            }
        ),
    )
    dry_run = forms.BooleanField(
        label="dry_run",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input mx-2"}),
    )
