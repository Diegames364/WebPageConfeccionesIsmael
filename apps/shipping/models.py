from django.db import models

class ShippingZone(models.Model):
    name = models.CharField(max_length=80, unique=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Zona de envío"
        verbose_name_plural = "Zonas de envío"
        ordering = ["name"]

    def __str__(self) -> str:
        status = "Activa" if self.is_active else "Inactiva"
        return f"{self.name} (${self.cost}) - {status}"
