from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField("Teléfono", max_length=20, blank=True)
    address = models.CharField("Dirección", max_length=255, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.email or self.user.username}"
