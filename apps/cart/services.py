from django.db import transaction
from django.db.models import F

from .models import Cart, CartItem


def get_or_create_cart(request):
    # Asegura que exista sesión
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None

    cart = Cart.objects.filter(is_active=True).filter(
        user=user if user else None,
        session_key=session_key if not user else ""
    ).first()

    if not cart:
        cart = Cart.objects.create(
            session_key=session_key if not user else "",
            user=user,
            is_active=True
        )

    return cart


@transaction.atomic
def add_to_cart(cart: Cart, variant, qty: int = 1):
    """
    Suma qty a un item (o lo crea). Valida stock.
    """
    qty = int(qty or 1)
    if qty < 1:
        qty = 1

    # stock real
    if variant.stock <= 0:
        raise ValueError("Esta variante no tiene stock.")

    item, created = CartItem.objects.select_for_update().get_or_create(
        cart=cart,
        variant=variant,
        defaults={"quantity": 0},
    )

    new_qty = item.quantity + qty
    if new_qty > variant.stock:
        raise ValueError(f"Stock insuficiente. Disponible: {variant.stock}.")

    item.quantity = new_qty
    item.save(update_fields=["quantity"])
    return item


@transaction.atomic
def set_qty(cart: Cart, item_id: int, qty: int):
    """
    Setea cantidad FINAL. Si qty <= 0 elimina.
    Valida stock de manera fuerte.
    Retorna CartItem actualizado o None si se eliminó.
    """
    item = CartItem.objects.select_related("variant").select_for_update().get(pk=item_id, cart=cart)

    if qty <= 0:
        item.delete()
        return None

    # Validación stock
    if qty > item.variant.stock:
        raise ValueError(f"Stock insuficiente. Disponible: {item.variant.stock}.")

    item.quantity = qty
    item.save(update_fields=["quantity"])
    return item


@transaction.atomic
def remove_item(cart: Cart, item_id: int):
    CartItem.objects.filter(pk=item_id, cart=cart).delete()


@transaction.atomic
def clear_cart(cart: Cart):
    cart.items.all().delete()
