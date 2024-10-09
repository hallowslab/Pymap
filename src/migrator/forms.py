import json
import logging
import re
from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

from .models import UserPreferences

logger = logging.getLogger(__name__)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class JSONPrettyWidget(forms.Textarea):
    def format_value(self, value: str) -> str:
        # Pretty print the value before rendering
        try:
            value = json.loads(value)  # Ensure it's valid JSON
            return json.dumps(value, indent=4)
        except (TypeError, ValueError):
            return value  # If it's invalid, return as is


class PreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ["host_patterns"]

    def clean_host_patterns(self):
        patterns = self.data.get("host_patterns")
        try:
            if patterns:
                # Load the JSON string into a Python object (list)
                patterns_list = json.loads(patterns)

                # Clean each pattern by removing whitespace
                cleaned_patterns = [
                    [re.sub(r"\s+", "", pattern) for pattern in sublist]
                    for sublist in patterns_list
                ]

                # Return the cleaned list (not JSON string, just the Python object)
                return cleaned_patterns
        except (ValueError, TypeError):
            raise forms.ValidationError("Invalid JSON format")


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
        widget=forms.CheckboxInput(attrs={"class": "form-check-input mx-2 mt-2"}),
    )
