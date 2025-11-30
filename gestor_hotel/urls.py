"""
URL configuration for gestor_hotel project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from hotel import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),

    # NUEVAS RUTAS - Búsqueda por fechas
    path('buscar/', views.buscar_habitaciones, name='buscar_habitaciones'),
    path('disponibles/<str:fecha_entrada>/<str:fecha_salida>/',
        views.habitaciones_disponibles,
        name='habitaciones_disponibles'),

    # Rutas de habitaciones
    path('habitaciones/', views.lista_habitaciones, name='lista_habitaciones'),

    # Rutas de reservas (modificadas para soportar fechas)
    path('reservar/<int:habitacion_id>/', views.hacer_reserva, name='hacer_reserva'),
    path('reservar/<int:habitacion_id>/<str:fecha_entrada>/<str:fecha_salida>/',
        views.hacer_reserva,
        name='hacer_reserva_con_fechas'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),

    # Gestión (admin)
    path('reservas/', views.gestionar_reservas, name='gestionar_reservas'),
    path('reserva/<int:reserva_id>/cambiar-estado/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('habitacion/<int:habitacion_id>/cambiar-estado/', views.cambiar_estado_habitacion, name='cambiar_estado_habitacion'),
    path('agregar-habitacion/', views.agregar_habitacion, name='agregar_habitacion'),

    # Autenticación
    path('registrarse/', views.registrarse, name='registrarse'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='iniciar_sesion'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='cerrar_sesion'),
]