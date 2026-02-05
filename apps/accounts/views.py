from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm, ProfileForm
from .models import Profile


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]

        # Autentica usando el email (EmailBackend)
        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, "Correo o contraseña incorrectos.")
        else:
            login(request, user)
            messages.success(request, "Bienvenido/a 👋")
            return redirect("core:home")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada.")
    return redirect("core:home")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password1"]
        
        # Crea el usuario (username = email)
        User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=form.cleaned_data.get("first_name", ""),
            last_name=form.cleaned_data.get("last_name", ""),
        )

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Cuenta creada correctamente ✅")
            return redirect("accounts:profile")

        messages.success(request, "Cuenta creada. Ahora inicia sesión.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    form = ProfileForm(
        request.POST or None,
        initial={"phone": profile.phone, "address": profile.address},
    )

    if request.method == "POST" and form.is_valid():
        profile.phone = form.cleaned_data["phone"]
        profile.address = form.cleaned_data["address"]
        profile.save()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {"form": form})


# =======================================================
#  NUEVA VISTA: ELIMINAR CUENTA
# =======================================================
@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        logout(request)
        messages.success(request, "Tu cuenta ha sido eliminada permanentemente.")
        return redirect("core:home")
    
    return redirect("accounts:profile")