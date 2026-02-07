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
            attr_name = key.replace("attr_", "")
            attr_filters[attr_name] = value

    products = Product.objects.filter(is_active=True)

    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    if min_price is not None:
        products = products.filter(variants__price__gte=min_price).distinct()
    if max_price is not None:
        products = products.filter(variants__price__lte=max_price).distinct()

    if in_stock:
        products = products.filter(variants__stock__gt=0).distinct()

    # Filtros dinámicos (e.g. ?attr_Color=Rojo)
    for attr_name, attr_val in attr_filters.items():
        products = products.filter(
            variants__attributes__name__iexact=attr_name,
            variants__attributes__value__iexact=attr_val
        ).distinct()

    # Ordenamiento
    order_field = SORT_MAP.get(sort, "-created_at")
    products = products.order_by(order_field)

    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ---------------------------------------------------------
    # CORRECCIÓN DE FILTROS DUPLICADOS
    # ---------------------------------------------------------
    all_attrs = VariantAttribute.objects.filter(
        variant__product__is_active=True,
        variant__is_active=True
    ).values('name', 'value').distinct()

    attr_filters_sidebar = {}
    for item in all_attrs:
        raw_name = item['name']
        if not raw_name:
            continue
            
        # AQUÍ ESTÁ LA MAGIA: Limpiamos el nombre
        # " Talla " -> "Talla", "talla" -> "Talla"
        clean_name = raw_name.strip().capitalize()

        if clean_name not in attr_filters_sidebar:
            attr_filters_sidebar[clean_name] = []
        
        # Evitamos valores duplicados
        if item['value'] not in attr_filters_sidebar[clean_name]:
            attr_filters_sidebar[clean_name].append(item['value'])

    # Rangos de precio para el slider
    all_prices = Variant.objects.filter(product__is_active=True, is_active=True).aggregate(
        min_p=Min('price'),
        max_p=Max('price')
    )
    global_min = all_prices['min_p'] or 0
    global_max = all_prices['max_p'] or 1000

    # Mantener parámetros en la paginación
    query_params = request.GET.copy()
    if "page" in query_params:
        del query_params["page"]
    extra_params = query_params.urlencode()

    return render(request, "catalog/list.html", {
        "page_obj": page_obj,
        "q": q,
        "attr_filters_sidebar": attr_filters_sidebar, # Diccionario limpio
        "global_min": global_min,
        "global_max": global_max,
        "current_min": min_price,
        "current_max": max_price,
        "current_sort": sort,
        "in_stock": in_stock,
        "extra_params": extra_params,
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
        .prefetch_related("attributes")
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