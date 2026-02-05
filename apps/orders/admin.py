from django.contrib import admin
from django.db import transaction
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Order, OrderItem

# -----------------------------------------------------------------------------
# INLINE: LOS PRODUCTOS DENTRO DEL PEDIDO
# -----------------------------------------------------------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Agregamos Categoría y Color a la tabla
    fields = ("product_name", "get_category", "get_color", "variant_description", "unit_price_formatted", "quantity", "line_total_formatted")
    readonly_fields = ("product_name", "get_category", "get_color", "variant_description", "unit_price_formatted", "line_total_formatted")
    can_delete = False
    verbose_name = "Producto Comprado"
    verbose_name_plural = "🛒 Lista de Productos en este Pedido"

    # --- 1. MOSTRAR CATEGORÍA ---
    def get_category(self, obj):
        # Navegamos: Item -> Variante -> Producto -> Categoría
        if obj.variant and obj.variant.product.category:
            return obj.variant.product.category.name
        return "-"
    get_category.short_description = "Categoría"

    # --- 2. MOSTRAR COLOR (Con bolita) ---
    def get_color(self, obj):
        # Navegamos: Item -> Variante -> Color
        if obj.variant and obj.variant.color:
            color = obj.variant.color
            # Creamos la bolita visual + el nombre
            dot = f'<span style="display:inline-block; width:12px; height:12px; background-color:{color.hex_code}; border:1px solid #ccc; border-radius:50%; margin-right:5px; vertical-align:middle;"></span>'
            return mark_safe(f"{dot}{color.name}")
        return "-"
    get_color.short_description = "Color"

    def unit_price_formatted(self, obj):
        return f"${obj.unit_price}"
    unit_price_formatted.short_description = "Precio Unitario"

    def line_total_formatted(self, obj):
        return f"${obj.line_total}"
    line_total_formatted.short_description = "Subtotal Línea"


# -----------------------------------------------------------------------------
# ADMIN PRINCIPAL DE PEDIDOS
# -----------------------------------------------------------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Columnas principales de la lista
    list_display = ("id", "user_info", "status_colored", "total_formatted", "created_at", "items_count")
    list_filter = ("status", "created_at", "shipping_zone")
    search_fields = ("id", "customer_name", "customer_email") 
    readonly_fields = ("created_at", "updated_at")
    inlines = [OrderItemInline]
    
    ordering = ("-created_at",)

    # CORREGIDO: Ahora usamos tus campos reales (customer_address y shipping_zone)
    fieldsets = (
        ("Información del Cliente", {
            "fields": ("user", "customer_name", "customer_email", "customer_phone")
        }),
        ("Dirección de Envío", {
            "fields": ("customer_address", "shipping_zone", "shipping_cost", "is_pickup")
        }),
        ("Detalles del Pago y Notas", {
            "fields": ("payment_method", "notes")
        }),
        ("Estado del Pedido", {
            "fields": ("status", "total", "created_at", "updated_at")
        }),
    )

    # --- Funciones Visuales ---

    def user_info(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name} ({obj.user.email})"
        return f"{obj.customer_name} ({obj.customer_email})"
    user_info.short_description = "Cliente"

    def total_formatted(self, obj):
        return f"${obj.total}"
    total_formatted.short_description = "Total"

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"

    def status_colored(self, obj):
        colors = {
            "pending": "orange",
            "preparing": "blue",
            "shipped": "purple",
            "delivered": "green",
            "cancelled": "red",
        }
        color = colors.get(obj.status, "black")
        status_display = obj.get_status_display()
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{status_display.upper()}</span>')
    status_colored.short_description = "Estado"

    # --- Acciones Rápidas ---
    
    actions = ["mark_preparing", "mark_shipped", "mark_delivered", "mark_cancelled"]

    @admin.action(description="👨‍🍳 Marcar como PREPARANDO")
    def mark_preparing(self, request, queryset):
        queryset.update(status="preparing")

    @admin.action(description="🚚 Marcar como ENVIADO")
    def mark_shipped(self, request, queryset):
        queryset.update(status="shipped")

    @admin.action(description="🏁 Marcar como ENTREGADO")
    def mark_delivered(self, request, queryset):
        queryset.update(status="delivered")

    @admin.action(description="🚫 CANCELAR (Devuelve Stock)")
    def mark_cancelled(self, request, queryset):
        with transaction.atomic():
            for order in queryset.select_for_update():
                if order.status != "cancelled":
                    order.status = "cancelled"
                    order.save(update_fields=["status"])
                    order.restock_items() 

    def save_model(self, request, obj, form, change):
        if change:
            old = Order.objects.filter(pk=obj.pk).only("status").first()
            if old and old.status != "cancelled" and obj.status == "cancelled":
                obj.restock_items()
        super().save_model(request, obj, form, change)