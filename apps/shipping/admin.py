from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import ShippingZone

@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    # Columnas visuales
    list_display = ("name_bold", "cost_formatted", "status_visual")
    
    # Filtros y Búsqueda
    list_filter = ("is_active",)
    search_fields = ("name",)

    # Organización del formulario
    fieldsets = (
        ("📍 Ubicación y Costo", {
            "fields": ("name", "cost"),
            "description": "Defina el nombre del lugar y cuánto cuesta enviar allí."
        }),
        ("⚙️ Configuración", {
            "fields": ("is_active",),
            "description": "Desmarque esta casilla para dejar de ofrecer envíos a esta zona temporalmente."
        }),
    )

    # --- Métodos Visuales ---

    def name_bold(self, obj):
        return format_html('<b>{}</b>', obj.name)
    name_bold.short_description = "Nombre de la Zona"
    name_bold.admin_order_field = "name"

    def cost_formatted(self, obj):
        return f"${obj.cost}"
    cost_formatted.short_description = "Costo de Envío"
    cost_formatted.admin_order_field = "cost"

    def status_visual(self, obj):
        if obj.is_active:
            return mark_safe('<span style="color: green;">✅ Activa</span>')
        return mark_safe('<span style="color: red;">❌ Inactiva</span>')
    status_visual.short_description = "Disponibilidad"
    status_visual.admin_order_field = "is_active"