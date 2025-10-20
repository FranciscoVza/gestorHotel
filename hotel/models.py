from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
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
    precio_por_noche = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad_maxima = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Tipo de Habitación"
        verbose_name_plural = "Tipos de Habitación"
        indexes = [
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return self.get_nombre_display()


class Habitacion(models.Model):
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'En Mantenimiento'),
    ]

    numero = models.CharField(max_length=10, unique=True)
    tipo = models.ForeignKey(TipoHabitacion, on_delete=models.PROTECT, related_name='habitaciones') #Deleted Protec para evitar borrados sin querer
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    piso = models.IntegerField()
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['estado']),
        ]
        permissions = [
            ("can_change_room_state", "Can change room state"),
        ]

    def __str__(self):
        return f"Habitación {self.numero} - {self.tipo}"

    def esta_disponible(self, fecha_entrada=None, fecha_salida=None):
        """
        Verificar disponibilidad:
        - Si el estado != disponible -> no disponible.
        - Si no se pasan fechas -> verificar si existen reservas activas.
        - Si se pasan fechas -> verificar solapamiento (excluye reservas donde fecha_salida <= fecha_entrada nueva).
        """
        if self.estado != 'disponible':
            return False

        hoy = date.today()

        if not fecha_entrada or not fecha_salida:
            reservas_activas = self.reservas.filter(
                estado__in=['pendiente', 'confirmada'],
                fecha_salida__gte=hoy
            )
            return not reservas_activas.exists()

        # Validar rango
        if fecha_entrada >= fecha_salida:
            return False

        reservas_conflicto = self.reservas.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_entrada__lt=fecha_salida,
            fecha_salida__gt=fecha_entrada
        )
        return not reservas_conflicto.exists()

    def proximas_reservas(self, limite=3):
        return self.reservas.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_entrada__gte=date.today()
        ).order_by('fecha_entrada')[:limite]

    def reserva_actual(self):
        hoy = date.today()
        return self.reservas.filter(
            estado='confirmada',
            fecha_entrada__lte=hoy,
            fecha_salida__gt=hoy
        ).first()


class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]

    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas')
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='reservas')
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()
    numero_huespedes = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='pendiente')
    precio_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    comentarios = models.TextField(blank=True)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha_reserva']
        indexes = [
            models.Index(fields=['habitacion', 'fecha_entrada', 'fecha_salida']),
            models.Index(fields=['estado']),
        ]
        permissions = [
            ("can_confirm_reservation", "Can confirm reservation"),
            ("can_cancel_reservation", "Can cancel reservation"),
        ]

    def __str__(self):
        return f"Reserva #{self.id} - {self.cliente.username} - Hab. {self.habitacion.numero}"

    def clean(self):
        # Validaciones de integridad
        if self.fecha_entrada >= self.fecha_salida:
            raise ValidationError("La fecha de entrada debe ser anterior a la de salida.")
        if self.numero_huespedes < 1:
            raise ValidationError("La reserva debe tener al menos 1 huésped.")
        capacidad = self.habitacion.tipo.capacidad_maxima
        if self.numero_huespedes > capacidad:
            raise ValidationError(f"Número de huéspedes ({self.numero_huespedes}) excede la capacidad ({capacidad}).")

        # Verificar solapamiento con otras reservas confirmadas/pendientes
        conflictos = Reserva.objects.filter(
            habitacion=self.habitacion,
            estado__in=['pendiente', 'confirmada'],
            fecha_entrada__lt=self.fecha_salida,
            fecha_salida__gt=self.fecha_entrada
        )
        if self.pk:
            conflictos = conflictos.exclude(pk=self.pk)
        if conflictos.exists():
            raise ValidationError("La habitación no está disponible en ese rango de fechas.")

    def calcular_noches(self):
        return (self.fecha_salida - self.fecha_entrada).days

    def _calcular_precio(self):
        noches = Decimal(self.calcular_noches())
        precio_noche = Decimal(self.habitacion.tipo.precio_por_noche)
        return (noches * precio_noche).quantize(Decimal('0.01'))

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Ejecutar clean para validar
        self.full_clean()

        # Calcular precio si no está establecido
        if self.precio_total in (None, Decimal('0.00')):
            self.precio_total = self._calcular_precio()

        super().save(*args, **kwargs)

        # Actualizar estado de la habitación después de guardar
        self.actualizar_estado_habitacion()

    def actualizar_estado_habitacion(self):
        """
        Determina el estado de la habitación según reservas activas.
        - Si existe una reserva confirmada en curso -> ocupada.
        - Si no hay reservas activas -> disponible.
        - Si hay reservas pero no confirmadas -> mantener 'disponible' o 'mantenimiento' según negocio.
        """
        hoy = date.today()
        habitacion = self.habitacion

        # Si existe alguna reserva confirmada que incluye hoy -> ocupada
        if Reserva.objects.filter(habitacion=habitacion, estado='confirmada',
                                  fecha_entrada__lte=hoy, fecha_salida__gt=hoy).exists():
            habitacion.estado = 'ocupada'
            habitacion.save(update_fields=['estado'])
            return

        # Si no hay reservas activas (pendiente/confirmada) en o después de hoy -> disponible
        otras_reservas_activas = Reserva.objects.filter(
            habitacion=habitacion,
            estado__in=['pendiente', 'confirmada'],
            fecha_salida__gte=hoy
        ).exclude(id=self.id)

        if not otras_reservas_activas.exists():
            habitacion.estado = 'disponible'
            habitacion.save(update_fields=['estado'])

    def delete(self, *args, **kwargs):
        habitacion = self.habitacion
        super().delete(*args, **kwargs)

        hoy = date.today()
        reservas_activas = Reserva.objects.filter(
            habitacion=habitacion,
            estado__in=['pendiente', 'confirmada'],
            fecha_salida__gte=hoy
        )

        if not reservas_activas.exists():
            habitacion.estado = 'disponible'
            habitacion.save(update_fields=['estado'])


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil') #Para consultas claras
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.TextField(blank=True)
    cedula = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        indexes = [
            models.Index(fields=['cedula']),
        ]

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
