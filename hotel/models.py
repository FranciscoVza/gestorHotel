from django.db import models
from django.contrib.auth.models import User
from datetime import date

class TipoHabitacion(models.Model):
    TIPOS_HABITACION = [
        ('individual', 'Individual'),
        ('doble', 'Doble'),
        ('suite', 'Suite'),
        ('familiar', 'Familiar'),
    ]

    nombre = models.CharField(max_length=50, choices=TIPOS_HABITACION, unique=True)
    descripcion = models.TextField(blank=True)
    precio_por_noche = models.DecimalField(max_digits=8, decimal_places=2)
    capacidad_maxima = models.IntegerField()

    def __str__(self):
        return self.get_nombre_display()

    class Meta:
        verbose_name = "Tipo de Habitación"
        verbose_name_plural = "Tipos de Habitación"

class Habitacion(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'En Mantenimiento'),
    ]

    numero = models.CharField(max_length=10, unique=True)
    tipo = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    piso = models.IntegerField()
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Habitación {self.numero} - {self.tipo}"

    def esta_disponible(self, fecha_entrada=None, fecha_salida=None):
        """
        Verificar si la habitación está disponible considerando:
        1. Estado de la habitación
        2. Reservas existentes en el rango de fechas
        """
        # Si no está marcada como disponible, no está disponible
        if self.estado != 'disponible':
            return False

        # Si no se proporcionan fechas, verificar disponibilidad general
        if not fecha_entrada or not fecha_salida:
            # Verificar si tiene reservas activas (pendientes o confirmadas)
            reservas_activas = self.reserva_set.filter(
                estado__in=['pendiente', 'confirmada'],
                fecha_salida__gte=date.today()  # Reservas que no han terminado
            )
            return not reservas_activas.exists()

        # Verificar conflictos de fechas con reservas existentes
        reservas_conflicto = self.reserva_set.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_entrada__lt=fecha_salida,  # La reserva empieza antes de que termine la nueva
            fecha_salida__gt=fecha_entrada   # La reserva termina después de que empiece la nueva
        )

        return not reservas_conflicto.exists()

    def proximas_reservas(self):
        """Obtener las próximas reservas de esta habitación"""
        return self.reserva_set.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_entrada__gte=date.today()
        ).order_by('fecha_entrada')[:3]

    def reserva_actual(self):
        """Obtener la reserva actual si existe"""
        hoy = date.today()
        return self.reserva_set.filter(
            estado='confirmada',
            fecha_entrada__lte=hoy,
            fecha_salida__gt=hoy
        ).first()

    class Meta:
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"
        ordering = ['numero']

class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()
    numero_huespedes = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    comentarios = models.TextField(blank=True)

    def __str__(self):
        return f"Reserva #{self.id} - {self.cliente.username} - Hab. {self.habitacion.numero}"

    def calcular_noches(self):
        return (self.fecha_salida - self.fecha_entrada).days

    def save(self, *args, **kwargs):
        # Calcular precio si no está establecido
        if not self.precio_total:
            noches = self.calcular_noches()
            self.precio_total = noches * self.habitacion.tipo.precio_por_noche

        # Guardar la reserva
        super().save(*args, **kwargs)

        # Actualizar estado de la habitación automáticamente
        self.actualizar_estado_habitacion()

    def actualizar_estado_habitacion(self):
        """Actualizar el estado de la habitación basado en las reservas"""
        hoy = date.today()
        habitacion = self.habitacion

        # Si la reserva está confirmada y es para hoy o está en curso
        if (self.estado == 'confirmada' and
            self.fecha_entrada <= hoy <= self.fecha_salida):
            habitacion.estado = 'ocupada'
            habitacion.save()

        # Si la reserva fue cancelada o completada, verificar si liberar la habitación
        elif self.estado in ['cancelada', 'completada']:
            # Verificar si hay otras reservas activas para esta habitación
            otras_reservas_activas = Reserva.objects.filter(
                habitacion=habitacion,
                estado__in=['pendiente', 'confirmada'],
                fecha_salida__gte=hoy
            ).exclude(id=self.id)

            if not otras_reservas_activas.exists():
                habitacion.estado = 'disponible'
                habitacion.save()

    def delete(self, *args, **kwargs):
        # Antes de eliminar, actualizar el estado de la habitación
        habitacion = self.habitacion
        super().delete(*args, **kwargs)

        # Verificar si liberar la habitación
        hoy = date.today()
        reservas_activas = Reserva.objects.filter(
            habitacion=habitacion,
            estado__in=['pendiente', 'confirmada'],
            fecha_salida__gte=hoy
        )

        if not reservas_activas.exists():
            habitacion.estado = 'disponible'
            habitacion.save()

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_reserva']

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.TextField(blank=True)
    cedula = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"