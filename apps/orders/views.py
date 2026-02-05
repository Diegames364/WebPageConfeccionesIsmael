# Python estándar
import os
from io import BytesIO
from decimal import Decimal

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# Apps internas
from apps.cart.services import get_or_create_cart
from .forms import CheckoutForm
from .models import Order, OrderItem

# ReportLab (PDF)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader


STATUS_BADGE = {
    "pending": "bg-warning text-dark",
    "confirmed": "bg-primary",
    "preparing": "bg-info text-dark",
    "shipped": "bg-purple",
    "delivered": "bg-success",
    "cancelled": "bg-danger",
}



def _variant_desc(variant):
    attrs = list(variant.attributes.all())
    if not attrs:
        return ""
    return ", ".join([f"{a.name}: {a.value}" for a in attrs])


@require_http_methods(["GET", "POST"])
def checkout(request):
    cart = get_or_create_cart(request)

    if cart.items.count() == 0:
        messages.info(request, "Tu carrito está vacío.")
        return redirect("cart:detail")

    # Autollenado si está logueado
    initial = {}
    if request.user.is_authenticated:
        user = request.user
        initial = {
            "customer_name": user.get_full_name(),
            "customer_email": user.email,
        }
        if hasattr(user, "profile"):
            initial["customer_phone"] = user.profile.phone
            initial["customer_address"] = user.profile.address

    form = CheckoutForm(request.POST or None, initial=initial)

    subtotal = Decimal(str(cart.subtotal))
    shipping_cost_preview = Decimal("0.00")

    if request.method == "POST" and form.is_valid():
        delivery_mode = form.cleaned_data["delivery_mode"]
        zone = form.cleaned_data["shipping_zone"]

        is_pickup = delivery_mode == "pickup"
        if is_pickup:
            shipping_cost = Decimal("0.00")
            zone = None
        else:
            if not zone:
                messages.error(request, "Selecciona una zona de envío.")
                return render(request, "orders/checkout.html", {
                    "form": form,
                    "cart": cart,
                    "subtotal": subtotal,
                    "shipping_cost": shipping_cost_preview,
                    "total": subtotal + shipping_cost_preview,
                })
            shipping_cost = Decimal(str(zone.cost))

        total = subtotal + shipping_cost

        # 🔹 Generar instrucciones de pago
        method = (form.cleaned_data["payment_method"] or "").lower()

        if "acord" in method:
            instructions_text = "Te contactaremos para coordinar el pago y la entrega."
        elif "contra" in method:
            instructions_text = "Pagas al recibir el pedido (aplica en envíos)."
            if is_pickup:
                instructions_text += " Si eliges retiro en tienda, el pago se coordina en el local."
        elif "transfer" in method:
            instructions_text = "Te enviaremos los datos para transferencia y confirmación del pago."
        else:
            instructions_text = ""

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    status="pending",
                    customer_name=form.cleaned_data["customer_name"],
                    customer_phone=form.cleaned_data["customer_phone"],
                    customer_email=form.cleaned_data["customer_email"],
                    customer_address=form.cleaned_data["customer_address"],
                    notes=form.cleaned_data["notes"],
                    is_pickup=is_pickup,
                    shipping_zone=zone,
                    shipping_cost=shipping_cost,
                    subtotal=subtotal,
                    total=total,
                    payment_method=form.cleaned_data["payment_method"],
                    payment_instructions=instructions_text,
                )

                cart_items = cart.items.select_related(
                    "variant", "variant__product"
                ).prefetch_related(
                    "variant__attributes"
                )

                for item in cart_items:
                    v = item.variant

                    # 1) Validar stock
                    if item.quantity > v.stock:
                        raise ValueError(
                            f"Stock insuficiente para '{v.product.name}'. "
                            f"Disponible: {v.stock}, solicitado: {item.quantity}."
                        )

                    # 2) Descontar stock con bloqueo
                    updated = type(v).objects.filter(
                        pk=v.pk, stock__gte=item.quantity
                    ).update(stock=F("stock") - item.quantity)

                    if updated == 0:
                        raise ValueError(
                            f"Stock insuficiente para '{v.product.name}' (el stock cambió mientras comprabas)."
                        )

                    # 3) Crear item del pedido
                    OrderItem.objects.create(
                        order=order,
                        variant=v,
                        product_name=v.product.name,
                        variant_description=_variant_desc(v),
                        unit_price=v.price,
                        quantity=item.quantity,
                        line_total=v.price * item.quantity,
                    )

                # 4) Vaciar carrito
                cart.items.all().delete()

                # Guardar datos en perfil
                if request.user.is_authenticated and hasattr(request.user, "profile"):
                    profile = request.user.profile
                    profile.phone = form.cleaned_data["customer_phone"]
                    profile.address = form.cleaned_data["customer_address"]
                    profile.save()

        except ValueError as e:
            messages.error(request, str(e))
            return redirect("cart:detail")

        messages.success(request, f"Pedido #{order.id} creado correctamente.")
        return redirect("orders:success", order_id=order.id)

    # Preview de envío
    if form.is_bound and form.is_valid():
        if form.cleaned_data["delivery_mode"] == "delivery" and form.cleaned_data["shipping_zone"]:
            shipping_cost_preview = Decimal(str(form.cleaned_data["shipping_zone"].cost))

    return render(request, "orders/checkout.html", {
        "form": form,
        "cart": cart,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost_preview,
        "total": subtotal + shipping_cost_preview,
    })


def success(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=order_id)

    if order.user_id and (not request.user.is_authenticated or order.user_id != request.user.id):
        messages.error(request, "No tienes acceso a ese pedido.")
        return redirect("core:home")

    return render(request, "orders/success.html", {"order": order})


def receipt(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=order_id)

    if order.user_id and (not request.user.is_authenticated or order.user_id != request.user.id):
        messages.error(request, "No tienes acceso a ese recibo.")
        return redirect("core:home")

    return render(request, "orders/receipt.html", {"order": order})


@login_required
def my_orders(request):
    qs = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-created_at")
    return render(request, "orders/my_orders.html", {
        "orders": qs,
        "STATUS_BADGE": STATUS_BADGE,
    })


@login_required
def my_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        pk=order_id,
        user=request.user
    )
    return render(request, "orders/my_order_detail.html", {
        "order": order,
        "STATUS_BADGE": STATUS_BADGE,
    })

def receipt_pdf(request, order_id):
    """
    Recibo en PDF con diseño completo + logo centrado en cuadro redondeado
    Ruta del logo: media/branding/logo.png
    """
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        pk=order_id
    )

    # Seguridad: solo el dueño del pedido
    if order.user_id and (not request.user.is_authenticated or order.user_id != request.user.id):
        messages.error(request, "No tienes acceso a ese recibo.")
        return redirect("core:home")

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Helper dinero
    def money(x):
        try:
            return f"{Decimal(x):.2f}"
        except Exception:
            return "0.00"

    margin = 2 * cm
    header_y = height - margin
    y = header_y


    # =====================================================
    # LOGO EN CUADRO REDONDEADO
    # =====================================================
    box_w = 4 * cm
    box_h = 4 * cm
    box_x = width - margin - box_w
    box_y = header_y - box_h - 0.6 * cm


    p.setLineWidth(1)
    p.roundRect(box_x, box_y, box_w, box_h, radius=8, stroke=1, fill=0)

    logo_path = os.path.join(settings.MEDIA_ROOT, "branding", "logo.png")

    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            img_w, img_h = logo.getSize()
            scale = min(box_w / img_w, box_h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale
            draw_x = box_x + (box_w - draw_w) / 2
            draw_y = box_y + (box_h - draw_h) / 2
            p.drawImage(logo, draw_x, draw_y, draw_w, draw_h, mask="auto")
        except Exception:
            p.setFont("Helvetica-Bold", 10)
            p.drawCentredString(
                box_x + box_w / 2,
                box_y + box_h / 2 - 5,
                "Logo"
            )
    else:
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(
            box_x + box_w / 2,
            box_y + box_h / 2 - 5,
            "Logo (no disponible)"
        )

    # =====================================================
    # ENCABEZADO
    # =====================================================
    y = box_y - 1 * cm
    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin, header_y, "CONFECCIONES ISMAEL")
    y = header_y - 0.6 * cm

    p.setFont("Helvetica", 10)
    p.drawString(margin, y, "Recibo interno")
    p.setFont("Helvetica", 10)
    p.drawRightString(
        width - margin,
        header_y,
        f"Pedido #{order.id} — {order.created_at.strftime('%d/%m/%Y %H:%M')}"
    )

    y -= 1 * cm

    # =====================================================
    # CLIENTE
    # =====================================================
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Cliente")
    y -= 0.5 * cm

    p.setFont("Helvetica", 10)
    p.drawString(margin, y, f"Nombre: {order.customer_name or '(No especificado)'}")
    y -= 0.45 * cm
    p.drawString(margin, y, f"Teléfono: {order.customer_phone or '(No especificado)'}")
    y -= 0.45 * cm
    p.drawString(margin, y, f"Correo: {order.customer_email or '(No especificado)'}")
    y -= 0.45 * cm
    p.drawString(margin, y, f"Dirección: {order.customer_address or '(No especificado)'}")
    y -= 0.8 * cm

    # =====================================================
    # ENTREGA
    # =====================================================
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Entrega")
    y -= 0.5 * cm

    p.setFont("Helvetica", 10)
    if order.is_pickup:
        p.drawString(margin, y, "Retiro en tienda")
    else:
        zone = order.shipping_zone.name if order.shipping_zone else "(Sin zona)"
        p.drawString(
            margin,
            y,
            f"Envío a domicilio — Zona: {zone} — Costo: ${money(order.shipping_cost)}"
        )
    y -= 0.9 * cm

    # =====================================================
    # DETALLE (TABLA)
    # =====================================================
    table_data = [
        ["Producto", "Detalle", "P. Unit", "Cant", "Total"]
    ]

    for it in order.items.all():
        table_data.append([
            it.product_name,
            it.variant_description or "",
            f"${money(it.unit_price)}",
            str(it.quantity),
            f"${money(it.line_total)}",
        ])

    table = Table(
        table_data,
        colWidths=[6 * cm, 4 * cm, 2.5 * cm, 2 * cm, 2.5 * cm]
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, margin, y - len(table_data) * 18)
    y -= len(table_data) * 18 + 0.8 * cm

    # =====================================================
    # TOTALES
    # =====================================================
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(width - margin, y, f"Subtotal: ${money(order.subtotal)}")
    y -= 0.45 * cm
    p.drawRightString(width - margin, y, f"Envío: ${money(order.shipping_cost)}")
    y -= 0.45 * cm
    p.drawRightString(width - margin, y, f"Total: ${money(order.total)}")

    # =====================================================
    # FINAL
    # =====================================================
    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="recibo_{order.id}.pdf"'
    )
    response.write(pdf)
    return response
