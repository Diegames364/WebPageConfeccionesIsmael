# SISTEMA WEB DE VENTAS Y PRODUCTOS - Confecciones Ismael 

*Universidad Nacional de Chimborazo*
*Facultad de Ingenieria*
*Carrera de Tecnologias de la Informacion*

Plataforma web integral desarrollada en Django para la gestión comercial y operativa de la microempresa **Confecciones Ismael**. El sistema digitaliza el proceso de ventas, desde el catálogo de productos hasta la gestión de pedidos personalizados y control de inventario.

## 1. DESCRIPCION DEL PROYECTO

Este proyecto soluciona la problemática de la gestión manual de pedidos y ventas. Permite a los clientes navegar por un catálogo, realizar compras directas y, lo más importante, solicitar **confecciones personalizadas** subiendo una descripcion con los detalles de como quiere su producto.

Para la administración, ofrece un panel de control robusto para gestionar el ciclo de vida del pedido (Pendiente, En Confección, Terminado, Entregado), controlar el stock de materia prima y productos terminados, y visualizar reportes de ventas.

## 2. ARQUITECTURA Y TECNOLOGIAS
El desarrollo del proyecto se realizó aplicando el patrón de diseño MVT (Modelo–Vista–Template), propio del framework Django, lo que permite una adecuada separación de responsabilidades entre la lógica de negocio, la presentación de la interfaz de usuario y el manejo de los datos. Ademas se incorporaron librerias de Python que mejora la gestión de la pagina

## 2.1 Stack Tecnológico

* **Backend:** Python 3.10+, Django 6.0
* **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (ES6+).
* **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Producción).
* **Librerías Clave:**
    * `django-jazzmin`: Tema avanzado para el panel de administración.
    * `Pillow`: Procesamiento de imágenes para el catálogo y diseños personalizados.
    * `reportlab`: Generación de reportes PDF.

Para mas información revise el archivo requierements.txt donde se encuentra toda las tecnologias que se uso en este proyecto.

## 3. CARACTERÍSTICAS PRINCIPALES

### 3.1 Módulo de Cliente (Frontend)
* **Catálogo Interactivo:** Visualización de prendas con filtrado por categorías y detalles de atributos (tallas, colores).
* **Carrito de Compras Dinámico:** Gestión de items en tiempo real vía AJAX (sin recargas de página).
* **Pedidos Personalizados:** Formulario especializado para que los clientes suban diseños/logos y especifiquen medidas para prendas a medida.
* **Autenticación:** Registro e inicio de sesión de clientes para seguimiento de pedidos.

### 3.2 Módulo Administrativo (Backend)
* **Gestión de Inventario:** Control de stock de productos terminados con alertas de stock bajo.
* **Gestión de Pedidos:** Flujo de estados para monitorear el progreso de la confección (Recepción -> Producción -> Entrega).
* **Reportes:** Visualización de ventas e ingresos por periodo.
* **Interfaz Admin Mejorada:** Personalización del panel de administración (Jazzmin) para una mejor experiencia de usuario.


## 4.0 Estructura General del Proyecto
ProyectoWeb/
│── manage.py
│── requirements.txt
│
├── apps/
│   ├── accounts/      # Autenticación y usuarios
│   ├── cart/          # Carrito de compras
│   ├── billing/       # Facturación
│   ├── catalog/       # Catalogo 
│   ├── core/        # Nucleo
│   ├── custom/        # Acciones Personalizadas
│   ├── reports/        # Reportes
│   ├── shipping/        # Ventas
│
├── templates/         # Plantillas HTML
├── static/            # Archivos CSS y JS
├── media/             # Imágenes de productos
│
└── config/          # Configuración principal
    ├── settings.py
    ├── urls.py
    └── wsgi.py

## 5. INSTALACION Y DESPLIEGUE LOCAL
Para ejecutar el proyecto en un entorno local con fines de desarrollo o auditoría, se deben seguir los siguientes pasos técnicos:

### 5.1 Requisitos Previos
* Sistema Operativo: Windows 10/11, Linux o macOS.
* Intérprete Python version 3.0 o superior.
* Gestor de paquetes pip.
* Base de datos SQLite o PostgreSQL

### 5.2 Procedimiento de Instalacion

1.  *Descarga y extracción del proyecto:*
    Descarge el archivo ConfeccionesIsmael.zip en su directorio de trabajo.
    O desde el repositorio de GitHub

## ⚠️ Advertencia: Ejecución en modo Desarrollo

Este proyecto se encuentra configurado **por defecto en modo Producción**.  
Para poder ejecutarlo correctamente en un **entorno de Desarrollo (local)**, es necesario realizar algunos ajustes en la configuración.

---

### Configuración para Entorno de Desarrollo

Para ejecutar el proyecto localmente, es necesario ajustar la configuración predeterminada de producción:

####  1.1 Modificar `config/settings.py`

```python
DEBUG = True

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

Elimine o comente cualquier referencia a servicios externos de almacenamiento de imágenes (ej: Cloudinary).

#### 1.2 Configurar rutas de medios en `config/urls.py`

Agregue la siguiente configuración al final del archivo `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
```

#### 1.3 Verificar modelos

Revise que los campos de imagen en los modelos sigan la estructura estándar de Django:

```python
imagen = models.ImageField(upload_to='productos/')
```

#### 1.4 Configurar templates

Asegúrese de que las referencias a imágenes en las plantillas HTML utilicen el atributo `.url`:

```html
<img src="{{ producto.imagen.url }}" alt="{{ producto.nombre }}">
```

---

2.  *Creacion del Entorno Virtual:*
    Se recomienda aislar las dependencias del proyecto. Abra una terminal en la raiz del proyecto:
    bash
    python -m venv venv
    

3.  *Activacion del Entorno Virtual:*
    * Windows: venv\Scripts\activate
    * Linux/Mac: source venv/bin/activate

4.  *Instalacion de Dependencias:*
    Ejecute el siguiente comando para instalar las librerias requeridas:
    bash
    pip install -r requirements.txt
    

5.  *Migracion de Base de Datos:*
    Inicialice la estructura de la base de datos SQLite - PostgreSQL:
    bash
    python manage.py migrate
    

6.  *Creacion de Superusuario:*
    Genere credenciales para el acceso administrativo:
    bash
    python manage.py createsuperuser
    

7.  *Ejecucion del Servidor de Desarrollo:*
    Inicie el servicio local en el puerto 8000:
    bash
    python manage.py runserver
    

8.  *Acceso:*
    Navegue a http://127.0.0.1:8000/admin e ingrese con las credenciales creadas.

---

## 6. DESARROLLADOR

*Desarrollado por:* Diego Estalyn Pasto Macas
*Institucion:* Universidad Nacional de Chimborazo
*Facultad:* Facultad de Ingenieria
*Carrera:* Tecnologias de la Informacion

---

