from django.conf import settings
from django.db import models
from apps.catalog.models import Variant


class Cart(models.Model):
    # Para carrito sin login (sesión)
    session_key = models.CharField("Clave de sesión", max_length=40, blank=True, db_index=True)

    # Para carrito con login (opcional)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuario",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="carts",
    )

    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    def __str__(self) -> str:
        owner = self.user.username if self.user else (self.session_key or "sin-sesion")
        return f"Carrito ({owner})"

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="Carrito")
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT, related_name="cart_items", verbose_name="Variante")
    quantity = models.PositiveIntegerField("Cantidad", default=1)

    class Meta:
        verbose_name = "Ítem del carrito"
        verbose_name_plural = "Ítems del carrito"
        constraints = [
            models.UniqueConstraint(fields=["cart", "variant"], name="unique_variant_per_cart")
        ]

    def __str__(self) -> str:
        return f"{self.variant.product.name} x {self.quantity}"

    @property
    def unit_price(self):
        return self.variant.price

    @property
    def total(self):
        return self.unit_price * self.quantity
