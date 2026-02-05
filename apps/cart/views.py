from django.contrib import messages
from django.db.models import Sum, F as DJF
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST


from django.http import JsonResponse
from django.template.loader import render_to_string

from .services import get_or_create_cart    

from apps.catalog.models import Variant
from .models import CartItem
from .services import (
    get_or_create_cart,
    add_to_cart,
    set_qty,
    remove_item,
    clear_cart,
)


@require_http_methods(["GET"])
def cart_detail(request):
    cart = get_or_create_cart(request)
    items = (
        cart.items
        .select_related("variant", "variant__product")
        .prefetch_related("variant__attributes")
        .order_by("id")
    )
    return render(request, "cart/detail.html", {"cart": cart, "items": items})


@require_http_methods(["POST"])
def cart_add(request, variant_id):
    cart = get_or_create_cart(request)
    variant = get_object_or_404(
        Variant,
        pk=variant_id,
        is_active=True,
        product__is_active=True
    )

    qty = request.POST.get("qty", "1")
    try:
        qty = int(qty)
    except ValueError:
        qty = 1

    try:
        add_to_cart(cart, variant, qty)
        messages.success(request, "Producto agregado al carrito ✅")
    except ValueError as e:
        messages.error(request, str(e))

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "cart:detail"
    return redirect(next_url)


@require_http_methods(["POST"])
def cart_remove(request, item_id):
    cart = get_or_create_cart(request)
    remove_item(cart, item_id)
    messages.info(request, "Producto eliminado del carrito.")
    return redirect("cart:detail")


@require_http_methods(["POST"])
def cart_clear(request):
    cart = get_or_create_cart(request)
    clear_cart(cart)
    messages.info(request, "Carrito vaciado.")
    return redirect("cart:detail")


# -------------------------
# API JSON para actualizar cantidades sin recargar
# -------------------------

def _cart_count(cart) -> int:
    agg = cart.items.aggregate(c=Sum("quantity"))
    return int(agg["c"] or 0)


def _can_checkout(cart) -> bool:
    # True si todo ok (cantidad <= stock)
    return not cart.items.select_related("variant").filter(
        quantity__gt=DJF("variant__stock")
    ).exists()


@require_POST
def cart_item_api(request, item_id):
    """
    Recibe:
      - qty  (cantidad final)  OR
      - delta (+1 / -1)
    Devuelve:
      ok, deleted, item_qty, item_total, cart_subtotal, cart_count, can_checkout, items_left, stock
    """
    cart = get_or_create_cart(request)

    try:
        item = CartItem.objects.select_related("variant", "variant__product").get(pk=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Ítem no encontrado."}, status=404)

    qty = request.POST.get("qty")
    delta = request.POST.get("delta")

    try:
        if delta is not None and delta != "":
            qty_final = item.quantity + int(delta)
        else:
            qty_final = int(qty)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Cantidad inválida."}, status=400)

    try:
        updated_item = set_qty(cart, item_id, qty_final)  # si <=0, debe eliminar y retornar None
    except ValueError as e:
        item.variant.refresh_from_db()
        return JsonResponse({"ok": False, "error": str(e), "stock": item.variant.stock}, status=400)

    cart.refresh_from_db()

    count = _cart_count(cart)
    can_checkout = _can_checkout(cart)
    items_left = cart.items.count()

    if updated_item is None:
        return JsonResponse({
            "ok": True,
            "deleted": True,
            "cart_subtotal": str(cart.subtotal),
            "cart_count": count,
            "can_checkout": can_checkout,
            "items_left": items_left,
        })

    updated_item.refresh_from_db()
    updated_item.variant.refresh_from_db()

    return JsonResponse({
        "ok": True,
        "deleted": False,
        "item_qty": updated_item.quantity,
        "item_total": str(updated_item.total),
        "cart_subtotal": str(cart.subtotal),
        "cart_count": count,
        "can_checkout": can_checkout,
        "items_left": items_left,
        "stock": updated_item.variant.stock,
    })


# -------------------------
# API para navbar / mini-carrito
# -------------------------
@require_http_methods(["GET"])
def summary_api(request):
    cart = get_or_create_cart(request)

    items = (
        cart.items
        .select_related(
            "variant",
            "variant__product",
            "variant__variant_image",      
        )
        .prefetch_related(
            "variant__attributes",
            "variant__product__images",   
        )
        .order_by("id")[:8]
    )

    mini_cart_html = render_to_string(
        "cart/_mini_cart.html",
        {"cart": cart, "items": items},
        request=request
    )

    cart_count = sum(i.quantity for i in cart.items.all())

    return JsonResponse({
        "ok": True,
        "mini_cart_html": mini_cart_html,
        "cart_count": cart_count
    })
