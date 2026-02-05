from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("pedido/<int:order_id>/", views.success, name="success"),
    path("recibo/<int:order_id>/", views.receipt, name="receipt"),
    path("recibo/<int:order_id>/pdf/", views.receipt_pdf, name="receipt_pdf"),
    path("recibo/<int:order_id>/pdf/", views.receipt_pdf, name="receipt_pdf"),
    path("mis-pedidos/", views.my_orders, name="my_orders"),
    path("mis-pedidos/<int:order_id>/", views.my_order_detail, name="my_order_detail"),
]
