# hotel/management/commands/poblar_datos.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hotel.models import TipoHabitacion, Habitacion, PerfilUsuario

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos iniciales del hotel'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('INICIANDO POBLADO DE DATOS DEL HOTEL'))
        self.stdout.write('='*60)

        # Crear tipos de habitación
        tipos_habitacion = [
            {
                'nombre': 'individual',
                'descripcion': 'Habitación cómoda para una persona con cama individual y escritorio.',
                'precio_por_noche': 35000.00,
                'capacidad_maxima': 1
            },
            {
                'nombre': 'doble',
                'descripcion': 'Habitación espaciosa con cama matrimonial o dos camas individuales.',
                'precio_por_noche': 55000.00,
                'capacidad_maxima': 2
            },
            {
                'nombre': 'suite',
                'descripcion': 'Suite de lujo con sala de estar separada, cama king size y minibar.',
                'precio_por_noche': 95000.00,
                'capacidad_maxima': 2
            },
            {
                'nombre': 'familiar',
                'descripcion': 'Habitación amplia ideal para familias con múltiples camas y área de estar.',
                'precio_por_noche': 75000.00,
                'capacidad_maxima': 4
            }
        ]

        self.stdout.write('\nPASO 1: Creando tipos de habitación...')
        for tipo_data in tipos_habitacion:
            tipo, created = TipoHabitacion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Tipo "{tipo.get_nombre_display()}" - ${tipo.precio_por_noche}/noche')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Tipo "{tipo.get_nombre_display()}" ya existe')
                )

        # Crear habitaciones de ejemplo
        habitaciones_ejemplo = [
            # PISO 1 - Habitaciones económicas
            {'numero': '101', 'tipo': 'individual', 'piso': 1, 'descripcion': 'Habitación individual con vista al jardín y WiFi gratuito'},
            {'numero': '102', 'tipo': 'individual', 'piso': 1, 'descripcion': 'Habitación individual económica con baño privado'},
            {'numero': '103', 'tipo': 'individual', 'piso': 1, 'descripcion': 'Habitación individual con escritorio para trabajo'},
            {'numero': '104', 'tipo': 'doble', 'piso': 1, 'descripcion': 'Habitación doble estándar con balcón pequeño'},
            {'numero': '105', 'tipo': 'doble', 'piso': 1, 'descripcion': 'Habitación doble con vista al patio interior'},
            {'numero': '106', 'tipo': 'familiar', 'piso': 1, 'descripcion': 'Habitación familiar con área de juegos para niños'},

            # PISO 2 - Habitaciones intermedias
            {'numero': '201', 'tipo': 'doble', 'piso': 2, 'descripcion': 'Habitación doble con vista a la ciudad y minibar'},
            {'numero': '202', 'tipo': 'doble', 'piso': 2, 'descripcion': 'Habitación doble premium con bañera'},
            {'numero': '203', 'tipo': 'doble', 'piso': 2, 'descripcion': 'Habitación doble con terraza privada'},
            {'numero': '204', 'tipo': 'individual', 'piso': 2, 'descripcion': 'Habitación individual premium con vista panorámica'},
            {'numero': '205', 'tipo': 'familiar', 'piso': 2, 'descripcion': 'Habitación familiar con cocina pequeña y refrigerador'},
            {'numero': '206', 'tipo': 'suite', 'piso': 2, 'descripcion': 'Suite junior con jacuzzi y sala de estar'},

            # PISO 3 - Habitaciones premium y suites
            {'numero': '301', 'tipo': 'suite', 'piso': 3, 'descripcion': 'Suite presidencial con terraza privada y vista 360°'},
            {'numero': '302', 'tipo': 'suite', 'piso': 3, 'descripcion': 'Suite de lujo con chimenea y bar privado'},
            {'numero': '303', 'tipo': 'suite', 'piso': 3, 'descripcion': 'Suite ejecutiva con oficina y sala de reuniones'},
            {'numero': '304', 'tipo': 'doble', 'piso': 3, 'descripcion': 'Habitación doble premium con bañera de hidromasaje'},
            {'numero': '305', 'tipo': 'familiar', 'piso': 3, 'descripcion': 'Habitación familiar de lujo con sala de estar separada'},
            {'numero': '306', 'tipo': 'doble', 'piso': 3, 'descripcion': 'Habitación doble con vista al mar y balcón amplio'},

            # PISO 4 - Habitaciones especiales
            {'numero': '401', 'tipo': 'suite', 'piso': 4, 'descripcion': 'Penthouse suite con terraza, jacuzzi y servicio personalizado'},
            {'numero': '402', 'tipo': 'familiar', 'piso': 4, 'descripcion': 'Habitación familiar premium con dos baños y cocina completa'},
        ]

        self.stdout.write('\nPASO 2: Creando habitaciones del hotel...')
        contador_creadas = 0
        for hab_data in habitaciones_ejemplo:
            try:
                tipo_habitacion = TipoHabitacion.objects.get(nombre=hab_data['tipo'])
                habitacion, created = Habitacion.objects.get_or_create(
                    numero=hab_data['numero'],
                    defaults={
                        'tipo': tipo_habitacion,
                        'piso': hab_data['piso'],
                        'descripcion': hab_data['descripcion'],
                        'estado': 'disponible'
                    }
                )
                if created:
                    contador_creadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(f' Habitación {habitacion.numero} - {habitacion.tipo} (Piso {habitacion.piso})')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f' Habitación {habitacion.numero} ya existe')
                    )
            except TipoHabitacion.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f' Error: Tipo de habitación "{hab_data["tipo"]}" no encontrado')
                )

        self.stdout.write(f'\n  Total habitaciones creadas: {contador_creadas}')

        # Crear usuario administrador
        self.stdout.write('\nPASO 3: Creando usuarios de ejemplo...')

        # Administrador
        admin_user, created = User.objects.get_or_create(
            username='admin_hotel',
            defaults={
                'first_name': 'Administrador',
                'last_name': 'Hotel',
                'email': 'admin@hotel.com',
                'is_staff': True,
                'is_superuser': False,
            }
        )

        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            PerfilUsuario.objects.create(
                usuario=admin_user,
                telefono='+56 9 1234 5678',
                cedula='12345678-9',
                direccion='Hotel Principal, Av. Central 123, Talca'
            )
            self.stdout.write(
                self.style.SUCCESS('  Administrador: admin_hotel / admin123')
            )
        else:
            self.stdout.write(
                self.style.WARNING('  Usuario administrador ya existe')
            )

        # Cliente demo 1
        cliente1, created = User.objects.get_or_create(
            username='cliente_demo',
            defaults={
                'first_name': 'Juan Carlos',
                'last_name': 'Pérez González',
                'email': 'juan.perez@email.com',
                'is_staff': False,
                'is_superuser': False,
            }
        )

        if created:
            cliente1.set_password('cliente123')
            cliente1.save()
            PerfilUsuario.objects.create(
                usuario=cliente1,
                telefono='+56 9 8765 4321',
                cedula='98765432-1',
                direccion='Calle Los Aromos 456, Talca'
            )
            self.stdout.write(
                self.style.SUCCESS('  Cliente Demo 1: cliente_demo / cliente123')
            )
        else:
            self.stdout.write(
                self.style.WARNING('  Usuario cliente_demo ya existe')
            )

        # Cliente demo 2
        cliente2, created = User.objects.get_or_create(
            username='maria_client',
            defaults={
                'first_name': 'María',
                'last_name': 'Silva Rodríguez',
                'email': 'maria.silva@email.com',
                'is_staff': False,
                'is_superuser': False,
            }
        )

        if created:
            cliente2.set_password('maria123')
            cliente2.save()
            PerfilUsuario.objects.create(
                usuario=cliente2,
                telefono='+56 9 5555 1234',
                cedula='15975348-6',
                direccion='Pasaje Las Flores 789, Talca'
            )
            self.stdout.write(
                self.style.SUCCESS('  Cliente Demo 2: maria_client / maria123')
            )
        else:
            self.stdout.write(
                self.style.WARNING('  Usuario maria_client ya existe')
            )

        # Estadísticas finales
        self.stdout.write('\nRESUMEN FINAL')
        self.stdout.write('='*60)
        self.stdout.write(f'Tipos de habitación: {TipoHabitacion.objects.count()}')
        self.stdout.write(f'Total habitaciones: {Habitacion.objects.count()}')
        self.stdout.write(f'Total usuarios: {User.objects.count()}')
        self.stdout.write(f'Perfiles creados: {PerfilUsuario.objects.count()}')

        # Estadísticas por tipo
        self.stdout.write('\nHABITACIONES POR TIPO:')
        for tipo in TipoHabitacion.objects.all():
            cantidad = Habitacion.objects.filter(tipo=tipo).count()
            self.stdout.write(f'  • {tipo.get_nombre_display()}: {cantidad} habitaciones (${tipo.precio_por_noche}/noche)')

        # Estadísticas por piso
        self.stdout.write('\nHABITACIONES POR PISO:')
        for piso in range(1, 5):
            cantidad = Habitacion.objects.filter(piso=piso).count()
            if cantidad > 0:
                self.stdout.write(f'  • Piso {piso}: {cantidad} habitaciones')

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('¡DATOS INICIALES CREADOS EXITOSAMENTE!'))
        self.stdout.write('='*60)

        self.stdout.write('\nUSUARIOS DE PRUEBA:')
        self.stdout.write('  Administrador: admin_hotel / admin123')
        self.stdout.write('  Cliente 1: cliente_demo / cliente123')
        self.stdout.write('  Cliente 2: maria_client / maria123')

        self.stdout.write('\nPRÓXIMOS PASOS:')
        self.stdout.write('  1. python manage.py runserver')
        self.stdout.write('  2. Visitar: http://127.0.0.1:8000')
        self.stdout.write('  3. ¡Probar el sistema con los usuarios creados!')

        self.stdout.write('\n¡El gestor de hotel está listo para usar!')