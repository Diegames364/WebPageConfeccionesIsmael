from .services import get_or_create_cart

def cart_context(request):
    try:
        cart = get_or_create_cart(request)
        count = sum(i.quantity for i in cart.items.all())
    except Exception:
        count = 0
    return {"CART_COUNT": count}
