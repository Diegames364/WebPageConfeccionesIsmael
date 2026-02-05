from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("catalogo/", views.product_list, name="list"),
    path("catalogo/<slug:slug>/", views.product_detail, name="detail"),
]
