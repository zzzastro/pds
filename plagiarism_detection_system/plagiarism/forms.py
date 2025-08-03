from django import forms
from django.contrib.auth.models import User
import re
from .models import UserProfile  # Ensure UserProfile is defined correctly
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError


class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    # Modify profession to be a dropdown (ChoiceField)
    PROFESSION_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('researcher', 'Researcher'),
    ]
    profession = forms.ChoiceField(choices=PROFESSION_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'profession']
    
    # Server-side validation
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username.isalnum():  # Check if username is alphanumeric
            raise forms.ValidationError("Username must be alphanumeric (no special characters allowed).")
        if User.objects.filter(username=username).exists():  # Check if username is unique
            raise forms.ValidationError("Username already taken. Please choose a different username.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():  # Check if email is unique
            raise forms.ValidationError("Email already registered. Please use a different email.")
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        # Password validation: must have uppercase, number, special char, and be at least 8 characters long
        if len(password) < 8 or not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password) or not re.search(r"[!@#$%^&*]", password):
            raise forms.ValidationError("Password must be at least 8 characters long and include at least one uppercase letter, one number, and one special character.")
        
        return cleaned_data

class LoginForm(forms.Form):
    username_or_email = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        # Try to find a user by username or email
        user = None
        
        # Check if the input is an email or username
        if '@' in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                raise ValidationError("This email is not registered.")
        else:
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                raise ValidationError("This username is not registered.")
        
        # Now authenticate the user
        if user:
            user = authenticate(username=user.username, password=password)
            if user is None:
                raise ValidationError("Incorrect password.")
        
        return cleaned_data
