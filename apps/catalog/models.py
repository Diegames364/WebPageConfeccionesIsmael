from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError

# ==========================================
# 1. MODELO CATEGORÍA (Sin Imagen)
# ==========================================
class Category(models.Model):
    name = models.CharField("Nombre", max_length=100)
    slug = models.SlugField("Slug", max_length=120, unique=True, blank=True)
    description = models.TextField("Descripción", blank=True)
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ==========================================
# 2. MODELO COLOR
# ==========================================
class Color(models.Model):
    name = models.CharField("Nombre del Color", max_length=50) 
    hex_code = models.CharField("Código Hex", max_length=7, help_text="Ej: #0000FF") 
    
    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colores"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ==========================================
# 3. MODELO PRODUCTO
# ==========================================
class Product(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        related_name="products",
        verbose_name="Categoría",
        null=True, 
        blank=True
    )
    
    name = models.CharField("Nombre", max_length=160)
    slug = models.SlugField("Etiqueta", max_length=180, unique=True, blank=True)
    description = models.TextField("Descripción", blank=True)
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField("Fecha de creación", auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["category", "-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            i = 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Producto",
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField("Imagen", upload_to="products/")
    alt_text = models.CharField("Texto Alternativo", max_length=150, blank=True)

    class Meta:
        verbose_name = "Imagen de Producto"
        verbose_name_plural = "Imágenes de Producto"


# ==========================================
# 4. MODELO VARIANTE
# ==========================================
class Variant(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Producto",
        on_delete=models.CASCADE,
        related_name="variants"
    )
    
    color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        verbose_name="Color",
        related_name="variants",
        null=True,
        blank=True
    )
    
    variant_image = models.ForeignKey(
        ProductImage,
        verbose_name="Imagen de Variante",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_variants",
        help_text="Si se deja vacío, se usará la imagen principal del producto."
    )
    
    price = models.DecimalField("Precio", max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField("Stock", default=0)
    sku = models.CharField("Código SKU", max_length=60, blank=True)
    is_active = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Variante"
        verbose_name_plural = "Variantes"

    def clean(self):
        if self.variant_image and self.variant_image.product_id != self.product_id:
            raise ValidationError({"variant_image": "La imagen debe pertenecer al mismo producto."})

    def __str__(self) -> str:
        color_name = f" - {self.color.name}" if self.color else ""
        return f"{self.product.name}{color_name} - ${self.price}"


# ==========================================
# 5. ATRIBUTOS EXTRA
# ==========================================
class VariantAttribute(models.Model):
    variant = models.ForeignKey(
        Variant,
        verbose_name="Variante",
        on_delete=models.CASCADE,
        related_name="attributes"
    )
    name = models.CharField("Atributo", max_length=60)
    value = models.CharField("Valor", max_length=80)

    class Meta:
        verbose_name = "Atributo de Variante"
        verbose_name_plural = "Atributos de Variante"

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"