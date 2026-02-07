from django.contrib import admin
from django.db.models import Sum, Count
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import json
import datetime

from apps.orders.models import Order, OrderItem
from .models import Reporte

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        # 1. GESTIÓN DE FECHAS (FILTROS)
        # Si el usuario no elige fecha, mostramos los últimos 30 días por defecto
        hoy = timezone.now().date()
        inicio_mes = hoy - timedelta(days=30)

        fecha_inicio = request.GET.get('start_date', inicio_mes.strftime('%Y-%m-%d'))
        fecha_fin = request.GET.get('end_date', hoy.strftime('%Y-%m-%d'))

        # Convertimos strings a objetos date para usarlos en el filtro
        date_start_obj = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        date_end_obj = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        # Ajustamos el fin para que incluya todo el día (hasta las 23:59:59)
        date_end_inclusive = date_end_obj + timedelta(days=1)

        # 2. CONSULTAS FILTRADAS
        # Aplicamos el rango de fechas a todas las consultas
        ventas_rango = Order.objects.filter(
            created_at__range=[date_start_obj, date_end_inclusive]
        ).exclude(status__in=['cancelled', 'pending']) # Solo ventas reales

        ingresos_totales = ventas_rango.aggregate(Sum('total'))['total__sum'] or 0
        pedidos_totales = ventas_rango.count()
        ticket_promedio = ingresos_totales / pedidos_totales if pedidos_totales > 0 else 0

        # Datos Gráfico Estados (Dona)
        qs_estados = Order.objects.filter(created_at__range=[date_start_obj, date_end_inclusive])\
            .values('status').annotate(total=Count('id'))
        
        labels_estados = [self.traducir_estado(item['status']) for item in qs_estados]
        data_estados = [item['total'] for item in qs_estados]

        # Datos Gráfico Top Productos (Barras)
        # Filtramos los items por la fecha de creación del pedido
        qs_productos = OrderItem.objects.filter(order__created_at__range=[date_start_obj, date_end_inclusive])\
            .values('product_name')\
            .annotate(cantidad_vendida=Sum('quantity'))\
            .order_by('-cantidad_vendida')[:10] # Top 10 productos vendidos
        labels_productos = [item['product_name'] for item in qs_productos]
        data_productos = [item['cantidad_vendida'] for item in qs_productos]

        # 3. CONTEXTO
        context = {
            **self.admin_site.each_context(request),
            'title': f'Reporte de Ventas ({fecha_inicio} al {fecha_fin})',
            'filtros': {'start': fecha_inicio, 'end': fecha_fin}, 
            'summary': {
                'ingresos': ingresos_totales,
                'pedidos': pedidos_totales,
                'promedio': ticket_promedio,
            },
            'chart_data': {
                'estados_labels': json.dumps(labels_estados),
                'estados_data': json.dumps(data_estados),
                'productos_labels': json.dumps(labels_productos),
                'productos_data': json.dumps(data_productos),
            },
            'ultimos_pedidos': ventas_rango.order_by('-created_at')[:10]
        }

        return render(request, "admin/reports_dashboard.html", context)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    
    def traducir_estado(self, status):
        diccionario = {
            'pending': 'Pendiente', 'confirmed': 'Confirmado', 'preparing': 'En preparación',
            'shipped': 'Enviado', 'delivered': 'Entregado', 'cancelled': 'Cancelado'
        }
        return diccionario.get(status, status)