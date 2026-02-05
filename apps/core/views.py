from django.shortcuts import render
from apps.catalog.models import Product
import random

def home(request):
    products = list(
        Product.objects.filter(is_active=True)
    )

    featured_products = random.sample(
        products,
        min(len(products), 4)
    )

    return render(request, "core/home.html", {
        "featured_products": featured_products
    })


def ayuda(request):
    return render(request, "core/ayuda.html")


def faq(request):
    return render(request, "core/faq.html")


def contacto(request):
    return render(request, "core/contacto.html")
