from django.contrib import admin
from django.utils.html import mark_safe
from .models import Category, Color, Product, ProductImage, Variant, VariantAttribute

# ==========================================
# 1. CATEGORÍAS
# ==========================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'count_products')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def count_products(self, obj):
        count = obj.products.count()
        return f"{count} productos"
    count_products.short_description = "Cant. Productos"


# ==========================================
# 2. COLORES
# ==========================================
@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code', 'color_preview')
    search_fields = ('name', 'hex_code')
    
    def color_preview(self, obj):
        if obj.hex_code:
            return mark_safe(f'<div style="width:25px; height:25px; background-color:{obj.hex_code}; border:1px solid #ccc; border-radius:50%; box-shadow: 1px 1px 3px rgba(0,0,0,0.2);"></div>')
        return "No definido"
    color_preview.short_description = "Vista Previa"


# ==========================================
# 3. INLINES (Tablas dentro de Producto)
# ==========================================
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview_inline',)
    
    def preview_inline(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="height:60px; border-radius:4px;">')
        return ""
    preview_inline.short_description = "Vista previa"

class VariantAttributeInline(admin.TabularInline):
    model = VariantAttribute
    extra = 1

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0
    show_change_link = True
    fields = ('color', 'price', 'stock', 'sku', 'is_active')


# ==========================================
# 4. PRODUCTO PRINCIPAL
# ==========================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'estado_visual', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, VariantInline] 
    list_per_page = 20

    def estado_visual(self, obj):
        return mark_safe('<span style="color: green;">✅ Activo</span>') if obj.is_active else mark_safe('<span style="color: red;">❌ Inactivo</span>')
    estado_visual.short_description = "Estado"


# ==========================================
# 5. VARIANTES
# ==========================================
@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'price', 'stock', 'semaforo_stock', 'sku', 'is_active')
    list_editable = ['price', 'stock', 'is_active']
    list_filter = ('product__category', 'color', 'is_active')
    search_fields = ('product__name', 'sku')
    autocomplete_fields = ['product', 'color']
    inlines = [VariantAttributeInline]

    def semaforo_stock(self, obj):
        if obj.stock == 0:
            return mark_safe('<span style="color: red; font-weight: bold;">🔴</span>')
        elif obj.stock < 5:
            return mark_safe('<span style="color: orange; font-weight: bold;">🟠</span>')
        else:
            return mark_safe('<span style="color: green; font-weight: bold;">🟢</span>')
    semaforo_stock.short_description = "Estado"


# ==========================================
# 6. IMÁGENES DE PRODUCTO
# ==========================================
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('preview_chica', 'product_name')
    search_fields = ('product__name',)
    list_filter = ('product',)

    def preview_chica(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;">')
        return "Sin imagen"
    preview_chica.short_description = "Imagen"

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = "Producto"