from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"placeholder": "correo@ejemplo.com"}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"placeholder": "********"}))


class RegisterForm(forms.Form):
    first_name = forms.CharField(label="Nombres", max_length=150, required=False)
    last_name = forms.CharField(label="Apellidos", max_length=150, required=False)
    email = forms.EmailField(label="Correo")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if p1:
            validate_password(p1)
        return cleaned


class ProfileForm(forms.Form):
    phone = forms.CharField(label="Teléfono", max_length=20, required=False)
    address = forms.CharField(label="Dirección", max_length=255, required=False)