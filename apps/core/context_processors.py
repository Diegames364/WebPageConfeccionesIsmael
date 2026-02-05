import os

def site_context(request):
    return {
        "SITE_NAME": "Confecciones Ismael",
        "WHATSAPP_NUMBER": os.getenv("WHATSAPP_NUMBER", "593999999999"),
    }

from django.conf import settings

def site_settings(request):
    return {
        "WHATSAPP_NUMBER": getattr(settings, "WHATSAPP_NUMBER", ""),
    }
