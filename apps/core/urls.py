from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("ayuda/", views.ayuda, name="ayuda"),
    path("faq/", views.faq, name="faq"),
    path("contacto/", views.contacto, name="contacto"),
]