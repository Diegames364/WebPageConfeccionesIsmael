import re
from django import forms
from apps.shipping.models import ShippingZone

PHONE_DIGITS_RE = re.compile(r"^[0-9]{7,15}$")

ALLOWED_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "hotmail.es",
    "outlook.com", "outlook.es",
    "live.com", "live.es",
    "msn.com", "msn.es",
}

def _suggest_email_domain(domain: str):
    domain = (domain or "").lower().strip()
    if not domain:
        return None

    common = {
        "gmal.com": "gmail.com",
        "gmai.com": "gmail.com",
        "gmail.con": "gmail.com",
        "hotmial.com": "hotmail.com",
        "hotmil.com": "hotmail.com",
        "outlok.com": "outlook.com",
        "outllok.com": "outlook.com",
        "lve.com": "live.com",
    }

    if domain in common:
        return common[domain]

    import difflib
    matches = difflib.get_close_matches(domain, list(ALLOWED_EMAIL_DOMAINS), n=1, cutoff=0.75)
    return matches[0] if matches else None


class CheckoutForm(forms.Form):

    DELIVERY_CHOICES = [
        ("pickup", "Retiro en tienda"),
        ("delivery", "Envío a domicilio"),
    ]

    PAYMENT_CHOICES = [
        ("transferencia", "Transferencia"),
        ("contraentrega", "Contraentrega"),
    ]

    # ---------- Datos del cliente ----------
    customer_name = forms.CharField(
        label="Nombre",
        required=True,
        max_length=120,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-4",
            "placeholder": "Nombre completo",
            "autocomplete": "name",
        }),
    )

    customer_phone = forms.CharField(
        label="Teléfono",
        required=True,
        max_length=15,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-4",
            "placeholder": "0999999999",
            "autocomplete": "tel",
            "inputmode": "numeric",
            "maxlength": "15",
            "pattern": "^[0-9]{7,15}$",
        }),
    )

    customer_email = forms.EmailField(
        label="Correo",
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control rounded-4",
            "placeholder": "usuario@gmail.com",
            "autocomplete": "email",
            "pattern": "^[a-zA-Z0-9._%+-]+@(gmail\\.com|hotmail\\.com|hotmail\\.es|outlook\\.com|outlook\\.es|live\\.com|live\\.es|msn\\.com|msn\\.es)$",
        }),
    )

    notes = forms.CharField(
        label="Notas",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control rounded-4",
            "rows": 3,
            "placeholder": "Pedidos personalizados, detalles de talla/color, etc. (opcional)",
        }),
    )

    # ---------- Entrega ----------
    delivery_mode = forms.ChoiceField(
        label="Entrega",
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        initial="pickup",
    )

    customer_address = forms.CharField(
        label="Dirección",
        required=False,
        max_length=220,
        widget=forms.TextInput(attrs={
            "class": "form-control rounded-4",
            "placeholder": "Calle, número, referencia (solo si es envío)",
            "autocomplete": "street-address",
        }),
    )

    shipping_zone = forms.ModelChoiceField(
        label="Zona de envío",
        queryset=ShippingZone.objects.all().order_by("name"),
        required=False,
        empty_label="Seleccione una zona",
        widget=forms.Select(attrs={
            "class": "form-control rounded-4",
        }),
    )

    # ---------- Pago ----------
    payment_method = forms.ChoiceField(
        label="Método de pago",
        choices=PAYMENT_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            "class": "form-control rounded-4",
        }),
    )

    # ---------- Validaciones ----------
    def clean_customer_name(self):
        v = (self.cleaned_data.get("customer_name") or "").strip()
        if not v:
            raise forms.ValidationError("El nombre es obligatorio.")
        return v

    def clean_customer_phone(self):
        raw = (self.cleaned_data.get("customer_phone") or "").strip()
        digits = re.sub(r"\D", "", raw)

        if not PHONE_DIGITS_RE.match(digits):
            raise forms.ValidationError(
                "Teléfono inválido. Usa solo números (7 a 15 dígitos)."
            )
        return digits

    def clean_customer_email(self):
        v = (self.cleaned_data.get("customer_email") or "").strip().lower()
        if not v:
            raise forms.ValidationError("El correo es obligatorio.")

        domain = v.split("@", 1)[-1]

        if domain not in ALLOWED_EMAIL_DOMAINS:
            suggestion = _suggest_email_domain(domain)
            if suggestion:
                user = v.split("@", 1)[0]
                raise forms.ValidationError(
                    f"Correo inválido. ¿Quisiste decir {user}@{suggestion}?"
                )
            raise forms.ValidationError(
                "Correo inválido. Usa gmail, hotmail, outlook, live o msn."
            )
        return v

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("delivery_mode") == "delivery" and not cleaned.get("shipping_zone"):
            self.add_error("shipping_zone", "Selecciona una zona de envío.")
        return cleaned
