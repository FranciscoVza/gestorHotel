from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, timedelta
from decimal import Decimal
from .models import TipoHabitacion, Habitacion, Reserva
import time

# -------------------------
# Tests unitarios existentes
# -------------------------
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
        # Intentar crear una reserva overlapping
        r2 = Reserva(cliente=self.user, habitacion=self.hab, fecha_entrada=entrada, fecha_salida=salida + timedelta(days=1), numero_huespedes=1)
        with self.assertRaises(Exception):
            r2.full_clean()  # Debe lanzar ValidationError por conflicto

    def test_reserva_actual_actualiza_estado(self):
        entrada = date.today()
        salida = entrada + timedelta(days=2)
        r = Reserva.objects.create(cliente=self.user, habitacion=self.hab, fecha_entrada=entrada, fecha_salida=salida, numero_huespedes=1, estado='confirmada')
        self.hab.refresh_from_db()
        self.assertEqual(self.hab.estado, 'ocupada')


# -------------------------
# Tests de rendimiento
# -------------------------
class PerformanceTests(TestCase):
    def setUp(self):
        self.tipo = TipoHabitacion.objects.create(
            nombre='suite',
            precio_por_noche=Decimal('50000.00'),
            capacidad_maxima=4
        )
        self.hab = Habitacion.objects.create(numero='201', tipo=self.tipo, piso=2)
        self.user = User.objects.create_user(username='perf_user', password='pass')

    def test_creacion_masiva_reservas(self):
        """
        Prueba de rendimiento: crear 500 reservas consecutivas y medir tiempo.
        Se asegura que la operación sea rápida y eficiente.
        """
        start_time = time.time()

        for i in range(10000):
            entrada = date.today() + timedelta(days=i)
            salida = entrada + timedelta(days=1)
            Reserva.objects.create(
                cliente=self.user,
                habitacion=self.hab,
                fecha_entrada=entrada,
                fecha_salida=salida,
                numero_huespedes=1,
                precio_total=self.hab.tipo.precio_por_noche
            )

        duration = time.time() - start_time
        print(f"\n[Prueba de rendimiento] Tiempo para crear 500 reservas: {duration:.2f} segundos")
        self.assertLess(duration, 5, "La creación masiva de reservas es demasiado lenta.")

    def test_consulta_proximas_reservas(self):
        """
        Prueba de rendimiento: consulta de próximas reservas.
        Se asegura que la función `proximas_reservas` sea eficiente.
        """
        # Crear 100 reservas para test
        for i in range(100):
            Reserva.objects.create(
                cliente=self.user,
                habitacion=self.hab,
                fecha_entrada=date.today() + timedelta(days=i),
                fecha_salida=date.today() + timedelta(days=i+1),
                numero_huespedes=1,
                precio_total=self.hab.tipo.precio_por_noche
            )

        start_time = time.time()
        reservas = self.hab.proximas_reservas()
        duration = time.time() - start_time
        print(f"[Prueba de rendimiento] Consulta de próximas reservas: {duration:.4f} segundos")

        self.assertLess(duration, 0.5, "La consulta de próximas reservas es demasiado lenta.")
        self.assertEqual(len(reservas), 3, "Debe devolver las 3 próximas reservas.")
