from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('habitaciones/', views.lista_habitaciones, name='lista_habitaciones'),
    path('habitaciones-disponibles/<str:fecha_entrada>/<str:fecha_salida>/', views.habitaciones_disponibles, name='habitaciones_disponibles'),
    path('reservar/<int:habitacion_id>/', views.hacer_reserva, name='hacer_reserva'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('registrarse/', views.registrarse, name='registrarse'),

    # URLs de administración
    path('admin/reservas/', views.gestionar_reservas, name='gestionar_reservas'),
    path('admin/reserva/<int:reserva_id>/cambiar-estado/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('admin/habitacion/<int:habitacion_id>/cambiar-estado/', views.cambiar_estado_habitacion, name='cambiar_estado_habitacion'),
    path('admin/agregar-habitacion/', views.agregar_habitacion, name='agregar_habitacion'),
]