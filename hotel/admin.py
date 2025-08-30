from django.contrib import admin
from .models import TipoHabitacion, Habitacion, Reserva, PerfilUsuario

@admin.register(TipoHabitacion)
class TipoHabitacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_por_noche', 'capacidad_maxima']
    list_filter = ['nombre']
    search_fields = ['nombre', 'descripcion']

@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'tipo', 'piso', 'estado', 'fecha_creacion']
    list_filter = ['tipo', 'estado', 'piso']
    search_fields = ['numero', 'descripcion']
    ordering = ['numero']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'habitacion', 'fecha_entrada', 'fecha_salida', 'estado', 'precio_total']
    list_filter = ['estado', 'fecha_entrada', 'habitacion__tipo']
    search_fields = ['cliente__username', 'habitacion__numero']
    date_hierarchy = 'fecha_entrada'
    ordering = ['-fecha_reserva']

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'telefono', 'cedula']
    search_fields = ['usuario__username', 'cedula', 'telefono']