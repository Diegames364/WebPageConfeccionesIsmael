from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Min, Max, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.services import get_or_create_cart, add_to_cart
from .models import Product, Variant, VariantAttribute

SORT_MAP = {
    "newest": "-created_at",
    "name_asc": "name",
    "name_desc": "-name",
}


def _safe_decimal(v, default=None):
    if v is None or v == "":
        return default
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return default


def product_list(request):
    q = (request.GET.get("q") or "").strip()
    min_price = _safe_decimal(request.GET.get("min"))
    max_price = _safe_decimal(request.GET.get("max"))
    in_stock = request.GET.get("in_stock") == "1"
    sort = (request.GET.get("sort") or "newest").strip()

    # attr_color, attr_talla, attr_material...
    attr_filters = {}
    for key, value in request.GET.items():
        if key.startswith("attr_") and value:
            attr_name = key.replace("attr_", "").strip().lower()
            attr_filters[attr_name] = value.strip()

    products = Product.objects.filter(is_active=True)

    if q:
        products = products.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(slug__icontains=q)
        )

    variant_qs = Variant.objects.filter(is_active=True, product__in=products)

    if min_price is not None:
        variant_qs = variant_qs.filter(price__gte=min_price)
    if max_price is not None:
        variant_qs = variant_qs.filter(price__lte=max_price)
    if in_stock:
        variant_qs = variant_qs.filter(stock__gt=0)

    # AND de atributos
    for aname, aval in attr_filters.items():
        variant_qs = variant_qs.filter(
            attributes__name__iexact=aname,
            attributes__value__iexact=aval
        )

    products = products.filter(variants__in=variant_qs).distinct()

    # Precio mínimo para cards
    products = products.annotate(min_price=Min("variants__price"))

    # =========================================================
    # LÓGICA DE ORDENAMIENTO (Agrupando por Categoría)
    # =========================================================
    if sort == "newest":
        # Primero agrupa por categoría, luego por los más nuevos
        products = products.order_by("category__name", "-created_at")
    elif sort == "name_asc":
        products = products.order_by("category__name", "name")
    elif sort == "name_desc":
        products = products.order_by("category__name", "-name")
    elif sort == "price_asc":
        products = products.order_by("category__name", "min_price")
    elif sort == "price_desc":
        products = products.order_by("category__name", "-min_price")
    else:
        # Default fallback
        products = products.order_by("category__name", "-created_at")

    # Stats precio
    price_stats = Variant.objects.filter(is_active=True, product__is_active=True).aggregate(
        minp=Min("price"), maxp=Max("price")
    )

    # UI de atributos (con selected listo para template)
    attr_names = (
        VariantAttribute.objects
        .filter(variant__is_active=True, variant__product__is_active=True)
        .values_list("name", flat=True)
        .distinct()
        .order_by("name")
    )

    attr_ui = []
    for name in attr_names:
        slug = str(name).strip().lower()
        key = f"attr_{slug}"
        values = (
            VariantAttribute.objects
            .filter(
                name__iexact=name,
                variant__is_active=True,
                variant__product__is_active=True
            )
            .values_list("value", flat=True)
            .distinct()
            .order_by("value")
        )
        attr_ui.append({
            "label": name,
            "key": key,
            "values": list(values),
            "selected": request.GET.get(key, ""),
        })

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "catalog/list.html", {
        "page_obj": page_obj,
        "q": q,
        "min": request.GET.get("min", ""),
        "max": request.GET.get("max", ""),
        "in_stock": in_stock,
        "sort": sort,
        "price_stats": price_stats,
        "attr_ui": attr_ui,
        "get_params": request.GET,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related("images"),
        slug=slug,
        is_active=True
    )

    variants = (
        Variant.objects
        .filter(product=product, is_active=True)
        .select_related("variant_image")  
        .order_by("price")
    )

    if not variants.exists():
        return render(request, "catalog/detail.html", {
            "product": product,
            "variants": variants,
            "variant_choices": [],
        })


    variant_choices = []
    for v in variants:
        attrs = list(v.attributes.all())
        desc = ", ".join([f"{a.name}: {a.value}" for a in attrs]) if attrs else "Variante"


        image_url = ""
        if v.variant_image:
            image_url = v.variant_image.image.url
        else:
            first = product.images.first()
            if first:
                image_url = first.image.url

        variant_choices.append({
            "id": v.id,
            "label": desc,
            "price": str(v.price),
            "stock": v.stock,
            "image_url": image_url,  
            "color": {
                    "name": v.color.name,
                    "hex_code": v.color.hex_code
                } if v.color else None,
        })

    if request.method == "POST":
        variant_id = request.POST.get("variant_id")
        qty = request.POST.get("qty", "1")

        try:
            qty = int(qty)
        except ValueError:
            qty = 1

        qty = max(qty, 1)

        v = get_object_or_404(Variant, pk=variant_id, product=product, is_active=True)

        if v.stock <= 0:
            messages.error(request, "Esta variante no tiene stock.")
            return redirect("catalog:detail", slug=slug)

        if qty > v.stock:
            messages.error(request, f"Stock insuficiente. Disponible: {v.stock}.")
            return redirect("catalog:detail", slug=slug)

        cart = get_or_create_cart(request)
        added = add_to_cart(cart, v, qty)

        if not added:
            messages.error(request, "Esta variante no tiene stock.")
            return redirect("catalog:detail", slug=slug)

        messages.success(request, "Producto agregado al carrito ✅")
        return redirect("catalog:detail", slug=slug)

    return render(request, "catalog/detail.html", {
        "product": product,
        "variants": variants,
        "variant_choices": variant_choices,
    })