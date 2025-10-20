from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import TipoHabitacion, Habitacion, Reserva
from decimal import Decimal

class ModelTests(TestCase):
    def setUp(self):
        self.tipo = TipoHabitacion.objects.create(
            nombre='doble',
            precio_por_noche=Decimal('25000.00'),
            capacidad_maxima=2
        )
        self.hab = Habitacion.objects.create(numero='101', tipo=self.tipo, piso=1)
        self.user = User.objects.create_user(username='cliente', password='pass')

    def test_calcular_noches(self):
        entrada = date.today()
        salida = entrada + timedelta(days=3)
        r = Reserva(cliente=self.user, habitacion=self.hab, fecha_entrada=entrada, fecha_salida=salida, numero_huespedes=2)
        self.assertEqual(r.calcular_noches(), 3)

    def test_precio_total_autocalculado(self):
        entrada = date.today()
        salida = entrada + timedelta(days=2)
        r = Reserva(cliente=self.user, habitacion=self.hab, fecha_entrada=entrada, fecha_salida=salida, numero_huespedes=2)
        r.save()
        self.assertEqual(r.precio_total, Decimal('50000.00'))

    def test_no_disponible_por_conflicto(self):
        entrada = date.today() + timedelta(days=1)
        salida = entrada + timedelta(days=2)
        r1 = Reserva.objects.create(cliente=self.user, habitacion=self.hab, fecha_entrada=entrada, fecha_salida=salida, numero_huespedes=1, estado='confirmada')
        # intentar reservar overlapping
        r2 = Reserva(cliente=self.user, habitacion=self.hab, fecha_entrada=entrada + timedelta(days=0), fecha_salida=salida + timedelta(days=1), numero_huespedes=1)
        with self.assertRaises(Exception):
            r2.full_clean()  # clean debe lanzar ValidationError por conflicto

    def test_reserva_actual_actualiza_estado(self):
        entrada = date.today()
        salida = entrada + timedelta(days=2)
        r = Reserva.objects.create(cliente=self.user, habitacion=self.hab, fecha_entrada=entrada, fecha_salida=salida, numero_huespedes=1, estado='confirmada')
        self.hab.refresh_from_db()
        self.assertEqual(self.hab.estado, 'ocupada')
