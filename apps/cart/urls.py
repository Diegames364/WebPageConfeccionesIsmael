from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("carrito/", views.cart_detail, name="detail"),
    path("carrito/agregar/<int:variant_id>/", views.cart_add, name="add"),
    path("carrito/eliminar/<int:item_id>/", views.cart_remove, name="remove"),
    path("carrito/vaciar/", views.cart_clear, name="clear"),
    path("api/carrito/item/<int:item_id>/", views.cart_item_api, name="item_api"),
    path("api/carrito/summary/", views.summary_api, name="summary_api"),
]
