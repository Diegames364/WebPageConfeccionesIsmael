from django.db import models

class Reporte(models.Model):
    """
    Este modelo no crea una tabla en la BD. 
    Solo sirve para anclar la vista de reportes en el Admin.
    """
    class Meta:
        managed = False  
        verbose_name = "📊 Panel de Estadísticas"
        verbose_name_plural = "📊 Reportes de Ventas"
        app_label = 'reports' 