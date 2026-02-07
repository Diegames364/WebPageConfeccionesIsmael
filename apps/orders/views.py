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

from django.contrib.staticfiles import finders

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

def money(amount):
    if amount is None:
        return "0.00"
    return f"{amount:.2f}"

@login_required
# ==============================================================================
# FUNCIÓN FACTURA (receipt_pdf)
# ==============================================================================
@login_required
def receipt_pdf(request, order_id):
    # 1. Obtener la orden
    order = get_object_or_404(Order, id=order_id)

    # 2. Configurar el PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f"recibo_orden_{order.id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    margin = 2 * cm

    # =====================================================
    # 3. ENCABEZADO: DATOS EMPRESA (IZQUIERDA)
    # =====================================================
    y_header = height - 2 * cm
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y_header, "CONFECCIONES ISMAEL")
    p.setFont("Helvetica", 10)
    y_header -= 0.5 * cm
    #p.drawString(margin, y_header, "RUC: 1234567890001")
    #y_header -= 0.5 * cm
    p.drawString(margin, y_header, "Av. Rocafuerte y Carlos Maria")
    y_header -= 0.5 * cm
    p.drawString(margin, y_header, "Tel: 099 452 8554")
    y_header -= 0.5 * cm
    p.drawString(margin, y_header, f"Fecha: {order.created_at.strftime('%d/%m/%Y')}")

    # =====================================================
    # 4. LOGO (DESDE CLOUDINARY)
    # =====================================================
    logo_url = "https://res.cloudinary.com/det18qekc/image/upload/v1770385547/logo_yf5upb.png"

    logo_width = 4 * cm
    logo_x = width - margin - logo_width
    logo_y = height - 3.5 * cm 

    try:
        p.drawImage(ImageReader(logo_url), logo_x, logo_y, width=logo_width, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"Error al cargar logo desde Cloudinary: {e}")
    # =====================================================
    # 5. TÍTULO Y CLIENTE
    # =====================================================
    y = height - 5.5 * cm
    
    # Línea separadora
    p.setLineWidth(1)
    p.line(margin, y + 0.5*cm, width - margin, y + 0.5*cm)

    # Título Centrado
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y, f"ORDEN DE PEDIDO #{order.id}")

    # Datos del Cliente
    y -= 1 * cm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(margin, y, "Facturar a:")
    
    p.setFont("Helvetica", 10)
    y -= 0.5 * cm
    
    # Validación de datos (para evitar errores si están vacíos)
    c_name = order.customer_name if order.customer_name else "Cliente General"
    c_address = order.customer_address if order.customer_address else "Dirección no registrada"
    c_phone = order.customer_phone if order.customer_phone else "Sin teléfono"
    c_email = order.user.email if (order.user and order.user.email) else "N/A"
    
    p.drawString(margin, y, f"Nombre: {c_name}")
    p.drawString(width/2, y, f"Teléfono: {c_phone}") 
    
    y -= 0.5 * cm
    p.drawString(margin, y, f"Dirección: {c_address}")
    p.drawString(width/2, y, f"Email: {c_email}")

    # =====================================================
    # 6. TABLA DE PRODUCTOS
    # =====================================================
    y -= 1.0 * cm
    
    data = [['Producto / Descripción', 'Cant.', 'Precio', 'Total']]
    
    for item in order.items.all():
        desc = item.product_name
        if item.variant_description:
            desc += f"\n({item.variant_description})"
            
        data.append([
            desc,
            str(item.quantity),
            f"${money(item.unit_price)}",
            f"${money(item.line_total)}"
        ])

    # Anchos calculados: 9.5 + 2 + 2.75 + 2.75 = 17cm (Ancho útil A4)
    col_widths = [9.5*cm, 2*cm, 2.75*cm, 2.75*cm]
    
    table = Table(data, colWidths=col_widths)

    estilo_tabla = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)), # Header oscuro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),                 # Texto blanco
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
    ]
    
    table.setStyle(TableStyle(estilo_tabla))

    w_table, h_table = table.wrapOn(p, width, height)
    
    # Salto de página si la tabla es muy larga
    if y - h_table < 2*cm:
        p.showPage()
        y = height - margin
        
    table.drawOn(p, margin, y - h_table)

    # =====================================================
    # 7. TOTALES
    # =====================================================
    y_final = y - h_table - 0.8*cm
    
    # Uso de Decimal("0.00") para asegurar matemáticas correctas
    shipping = order.shipping_cost if order.shipping_cost else Decimal("0.00")
    total = order.total if order.total else Decimal("0.00")
    subtotal = total - shipping

    p.setFont("Helvetica", 10)
    p.drawRightString(width - margin, y_final, f"Subtotal:   ${money(subtotal)}")
    
    y_final -= 0.6 * cm
    p.drawRightString(width - margin, y_final, f"Envío:   ${money(shipping)}")
    
    y_final -= 0.3 * cm
    p.setLineWidth(1)
    p.line(width - margin - 5*cm, y_final, width - margin, y_final)
    
    y_final -= 0.6 * cm
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - margin, y_final, f"TOTAL:   ${money(total)}")

    # Pie de página
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width/2, 2*cm, "Gracias por preferir Confecciones Ismael")

    p.showPage()
    p.save()
    return response