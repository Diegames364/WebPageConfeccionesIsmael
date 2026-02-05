from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import F

from apps.shipping.models import ShippingZone


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PREPARING = "preparing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_CONFIRMED, "Confirmado"),
        (STATUS_PREPARING, "En preparación"),
        (STATUS_SHIPPED, "Enviado"),
        (STATUS_DELIVERED, "Entregado"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    status = models.CharField(
        "Estado",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    # Usuario (para "Mis pedidos")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuario",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    # Datos del cliente (no obligatorios)
    customer_name = models.CharField("Nombre", max_length=120, blank=True)
    customer_phone = models.CharField("Teléfono", max_length=30, blank=True)
    customer_email = models.EmailField("Correo", blank=True)
    customer_address = models.CharField("Dirección", max_length=220, blank=True)
    notes = models.TextField("Notas", blank=True)

    # Envío / Retiro
    is_pickup = models.BooleanField("Retiro en tienda", default=False)
    shipping_zone = models.ForeignKey(
        ShippingZone,
        verbose_name="Zona de envío",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    shipping_cost = models.DecimalField("Costo de envío", max_digits=10, decimal_places=2, default=0)

    # Totales
    subtotal = models.DecimalField("Subtotal", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("Total", max_digits=10, decimal_places=2, default=0)

    # Pago
    payment_method = models.CharField(
        "Método de pago",
        max_length=30,
        default="Acordar",
        help_text="Acordar / Contraentrega / Transferencia",
    )
    payment_instructions = models.TextField(
    "Instrucciones de pago",
    blank=True,
    help_text="Texto que se mostrará al cliente según el método de pago elegido"
    )

    # Auditoría
    stock_reverted = models.BooleanField(default=False)
    created_at = models.DateTimeField("Creado", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado", auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Pedido #{self.id} - {self.get_status_display()}"

    def restock_items(self):
        """
        Reponer stock si el pedido se cancela (una sola vez).
        """
        if self.stock_reverted:
            return

        from apps.catalog.models import Variant

        with transaction.atomic():
            self.refresh_from_db()
            if self.stock_reverted:
                return

            for it in self.items.all():
                if it.variant_id:
                    Variant.objects.filter(pk=it.variant_id).update(
                        stock=F("stock") + it.quantity
                    )

            self.stock_reverted = True
            self.save(update_fields=["stock_reverted"])


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido"
    )

    # Snapshot del producto
    variant = models.ForeignKey(
        "catalog.Variant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Variante"
    )

    product_name = models.CharField("Producto", max_length=160)
    variant_description = models.CharField("Detalle", max_length=180, blank=True)
    unit_price = models.DecimalField("Precio unitario", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Cantidad", default=1)
    line_total = models.DecimalField("Total", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Ítem del pedido"
        verbose_name_plural = "Ítems del pedido"

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"
    
