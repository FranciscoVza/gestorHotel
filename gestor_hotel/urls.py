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
    path('habitaciones/', views.lista_habitaciones, name='lista_habitaciones'),
    path('reservar/<int:habitacion_id>/', views.hacer_reserva, name='hacer_reserva'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('registrarse/', views.registrarse, name='registrarse'),


    path('admin/reservas/', views.gestionar_reservas, name='gestionar_reservas'),
    path('admin/reserva/<int:reserva_id>/cambiar-estado/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('admin/habitacion/<int:habitacion_id>/cambiar-estado/', views.cambiar_estado_habitacion, name='cambiar_estado_habitacion'),
    path('admin/agregar-habitacion/', views.agregar_habitacion, name='agregar_habitacion'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='iniciar_sesion'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='cerrar_sesion'),
    path("accounts/logout/", LogoutView.as_view, name="logout"),
]