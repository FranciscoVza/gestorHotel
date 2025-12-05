from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from datetime import datetime, date, timedelta
from django.urls import reverse
from .models import Habitacion, Reserva, TipoHabitacion, PerfilUsuario
from .forms import ReservaForm, HabitacionForm, TipoHabitacionForm, RegistroUsuarioForm
from .email_utils import enviar_confirmacion_reserva



def es_administrador(user):
    return user.is_staff or user.is_superuser

def inicio(request):
    # Solo mostrar habitaciones realmente disponibles (sin reservas pendientes/confirmadas)
    habitaciones_disponibles = []
    todas_habitaciones = Habitacion.objects.filter(estado='disponible')

    for habitacion in todas_habitaciones:
        if habitacion.esta_disponible():
            habitaciones_disponibles.append(habitacion)

    # Limitar a 6 para la página de inicio
    habitaciones_disponibles = habitaciones_disponibles[:6]

    tipos_habitacion = TipoHabitacion.objects.all()

    contexto = {
        'habitaciones_disponibles': habitaciones_disponibles,
        'tipos_habitacion': tipos_habitacion,
        'es_admin': es_administrador(request.user) if request.user.is_authenticated else False,
        'hoy': date.today().isoformat(),  # Para el formulario de búsqueda
    }
    return render(request, 'hotel/inicio.html', contexto)

def actualizar_reservas_vencidas():
    ahora = timezone.now()
    vencidas = Reserva.objects.filter(fecha_salida__lt=ahora, estado="confirmada")

    for r in vencidas:
        if r.habitacion:
            r.estado = "completada"
            r.habitacion.disponible = True
            r.habitacion.save()
        else:
            print(f"⚠️ Reserva sin habitación: ID {r.id}")
        r.save()


# NUEVA VISTA: Búsqueda inicial de habitaciones por fechas
def buscar_habitaciones(request):
    """Vista inicial donde el cliente selecciona las fechas de su estadía"""
    if request.method == 'POST':
        fecha_entrada_str = request.POST.get('fecha_entrada')
        fecha_salida_str = request.POST.get('fecha_salida')

        # Validaciones básicas
        if not fecha_entrada_str or not fecha_salida_str:
            messages.error(request, 'Debe seleccionar ambas fechas')
            return render(request, 'hotel/buscar_habitaciones.html', {
                'hoy': date.today().isoformat()
            })

        # Convertir strings a objetos date
        try:
            fecha_entrada = date.fromisoformat(fecha_entrada_str)
            fecha_salida = date.fromisoformat(fecha_salida_str)
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')
            return render(request, 'hotel/buscar_habitaciones.html', {
                'hoy': date.today().isoformat()
            })

        # Validar que las fechas sean lógicas
        if fecha_entrada < date.today():
            messages.error(request, 'La fecha de entrada no puede ser anterior a hoy')
            return render(request, 'hotel/buscar_habitaciones.html', {
                'hoy': date.today().isoformat()
            })

        if fecha_entrada >= fecha_salida:
            messages.error(request, 'La fecha de salida debe ser posterior a la fecha de entrada')
            return render(request, 'hotel/buscar_habitaciones.html', {
                'hoy': date.today().isoformat()
            })

        # Obtener tipo (opcional) y redirigir a la vista de habitaciones disponibles
        tipo = request.POST.get('tipo')
        url = reverse('habitaciones_disponibles', kwargs={
            'fecha_entrada': fecha_entrada_str,
            'fecha_salida': fecha_salida_str,
        })
        if tipo:
            url = f"{url}?tipo={tipo}"
        return redirect(url)

    return render(request, 'hotel/buscar_habitaciones.html', {
        'hoy': date.today().isoformat()
    })


# NUEVA VISTA: Mostrar habitaciones disponibles según fechas
def habitaciones_disponibles(request, fecha_entrada, fecha_salida):
    """Muestra solo las habitaciones disponibles para el rango de fechas especificado"""
    try:
        fecha_entrada_obj = date.fromisoformat(fecha_entrada)
        fecha_salida_obj = date.fromisoformat(fecha_salida)
    except ValueError:
        messages.error(request, 'Fechas inválidas')
        return redirect('buscar_habitaciones')

    # Validar fechas nuevamente (por si acceden directamente a la URL)
    if fecha_entrada_obj < date.today() or fecha_entrada_obj >= fecha_salida_obj:
        messages.error(request, 'Rango de fechas inválido')
        return redirect('buscar_habitaciones')

    # Obtener todas las habitaciones
    todas_habitaciones = Habitacion.objects.select_related('tipo').all()

    # Filtrar solo las disponibles para estas fechas
    habitaciones_disponibles_list = []
    for habitacion in todas_habitaciones:
        if habitacion.esta_disponible(fecha_entrada_obj, fecha_salida_obj):
            habitaciones_disponibles_list.append(habitacion)

    # Agrupar por tipo para mejor presentación
    tipos_disponibles = {}
    for habitacion in habitaciones_disponibles_list:
        tipo_nombre = habitacion.tipo.get_nombre_display()
        if tipo_nombre not in tipos_disponibles:
            tipos_disponibles[tipo_nombre] = {
                'tipo': habitacion.tipo,
                'habitaciones': []
            }
        tipos_disponibles[tipo_nombre]['habitaciones'].append(habitacion)

    # Calcular número de noches
    noches = (fecha_salida_obj - fecha_entrada_obj).days

    # Aplicar filtros adicionales si existen
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        habitaciones_disponibles_list = [
            h for h in habitaciones_disponibles_list
            if h.tipo.nombre == tipo_filtro
        ]

    contexto = {
        'fecha_entrada': fecha_entrada_obj,
        'fecha_salida': fecha_salida_obj,
        'fecha_entrada_str': fecha_entrada,
        'fecha_salida_str': fecha_salida,
        'noches': noches,
        'tipos_disponibles': tipos_disponibles,
        'habitaciones_disponibles': habitaciones_disponibles_list,
        'todos_tipos': TipoHabitacion.objects.all(),
        'tipo_seleccionado': tipo_filtro,
        'es_admin': es_administrador(request.user) if request.user.is_authenticated else False,
    }

    return render(request, 'hotel/habitaciones_disponibles.html', contexto)


# MODIFICADA: Lista de habitaciones (para admin)
def lista_habitaciones(request):
    """Vista de administración para ver todas las habitaciones"""
    actualizar_reservas_vencidas()

    habitaciones = Habitacion.objects.all().order_by('numero')
    tipos = TipoHabitacion.objects.all()

    # Filtros
    tipo_filtro = request.GET.get('tipo')
    estado_filtro = request.GET.get('estado')
    disponibilidad_filtro = request.GET.get('disponibilidad')

    if tipo_filtro:
        habitaciones = habitaciones.filter(tipo__nombre=tipo_filtro)
    if estado_filtro:
        habitaciones = habitaciones.filter(estado=estado_filtro)

    # Filtro por disponibilidad real
    if disponibilidad_filtro == 'disponible':
        habitaciones_filtradas = []
        for habitacion in habitaciones:
            if habitacion.esta_disponible():
                habitaciones_filtradas.append(habitacion)
        habitaciones = habitaciones_filtradas
    elif disponibilidad_filtro == 'reservada':
        habitaciones_filtradas = []
        for habitacion in habitaciones:
            if not habitacion.esta_disponible():
                habitaciones_filtradas.append(habitacion)
        habitaciones = habitaciones_filtradas

    contexto = {
        'habitaciones': habitaciones,
        'tipos': tipos,
        'es_admin': es_administrador(request.user) if request.user.is_authenticated else False,
        'tipo_seleccionado': tipo_filtro,
        'estado_seleccionado': estado_filtro,
        'disponibilidad_seleccionada': disponibilidad_filtro,
    }
    return render(request, 'hotel/habitaciones.html', contexto)


# MODIFICADA: Hacer reserva ahora acepta fechas desde la URL
@login_required
def hacer_reserva(request, habitacion_id, fecha_entrada=None, fecha_salida=None):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)

    # Convertir fechas si vienen desde la URL
    fecha_entrada_obj = None
    fecha_salida_obj = None

    if fecha_entrada and fecha_salida:
        try:
            fecha_entrada_obj = date.fromisoformat(fecha_entrada)
            fecha_salida_obj = date.fromisoformat(fecha_salida)
        except ValueError:
            messages.error(request, 'Fechas inválidas')
            return redirect('buscar_habitaciones')

        # Verificar disponibilidad para esas fechas específicas
        if not habitacion.esta_disponible(fecha_entrada_obj, fecha_salida_obj):
            messages.error(request, 'Esta habitación ya no está disponible para esas fechas.')
            return redirect('habitaciones_disponibles',
                        fecha_entrada=fecha_entrada,
                        fecha_salida=fecha_salida)
    else:
        # Verificar disponibilidad general
        if not habitacion.esta_disponible():
            messages.error(request, 'Esta habitación no está disponible para reservas.')
            return redirect('lista_habitaciones')

    if request.method == 'POST':
        form = ReservaForm(request.POST)

        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.habitacion = habitacion
            reserva.cliente = request.user

            # Obtener fechas desde el form
            fecha_entrada_form = reserva.fecha_entrada
            fecha_salida_form = reserva.fecha_salida

            # Validaciones manuales antes de guardar
            if fecha_entrada_form < date.today():
                messages.error(request, 'La fecha de entrada no puede ser anterior a hoy.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas(),
                    'fecha_entrada_preseleccionada': fecha_entrada,
                    'fecha_salida_preseleccionada': fecha_salida,
                })

            if fecha_salida_form <= fecha_entrada_form:
                messages.error(request, 'La fecha de salida debe ser posterior a la fecha de entrada.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas(),
                    'fecha_entrada_preseleccionada': fecha_entrada,
                    'fecha_salida_preseleccionada': fecha_salida,
                })

            # Verificar disponibilidad en el rango solicitado
            if not habitacion.esta_disponible(fecha_entrada_form, fecha_salida_form):
                messages.error(request, 'La habitación no está disponible en esas fechas.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas(),
                    'fecha_entrada_preseleccionada': fecha_entrada,
                    'fecha_salida_preseleccionada': fecha_salida,
                })

            # Validar capacidad
            capacidad_max = habitacion.tipo.capacidad_maxima
            if reserva.numero_huespedes > capacidad_max:
                messages.error(request, f'Esta habitación tiene capacidad máxima para {capacidad_max} huéspedes.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas(),
                    'fecha_entrada_preseleccionada': fecha_entrada,
                    'fecha_salida_preseleccionada': fecha_salida,
                })

            # Guardar la reserva
            reserva.save()

            messages.success(request, '¡Reserva realizada exitosamente! Tu reserva está pendiente de confirmación.')
            return redirect('mis_reservas')

    else:
        # Pre-llenar el formulario con las fechas si vienen desde la búsqueda
        initial_data = {}
        if fecha_entrada_obj and fecha_salida_obj:
            initial_data = {
                'fecha_entrada': fecha_entrada_obj,
                'fecha_salida': fecha_salida_obj,
            }
        form = ReservaForm(initial=initial_data)

    # Calcular precio estimado si hay fechas
    precio_estimado = None
    noches = None
    if fecha_entrada_obj and fecha_salida_obj:
        noches = (fecha_salida_obj - fecha_entrada_obj).days
        precio_estimado = habitacion.tipo.precio_por_noche * noches

    # Render inicial
    contexto = {
        'form': form,
        'habitacion': habitacion,
        'proximas_reservas': habitacion.proximas_reservas(),
        'fecha_entrada_preseleccionada': fecha_entrada,
        'fecha_salida_preseleccionada': fecha_salida,
        'precio_estimado': precio_estimado,
        'noches': noches,
    }

    return render(request, 'hotel/hacer_reserva.html', contexto)


@user_passes_test(es_administrador)
@user_passes_test(es_administrador)
def cambiar_estado_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    nuevo_estado = request.POST.get('nuevo_estado')

    if nuevo_estado in ['pendiente', 'confirmada', 'cancelada', 'completada']:
        estado_anterior = reserva.estado
        reserva.estado = nuevo_estado
        reserva.save()

        # Si se confirma la reserva, enviar correo
        if nuevo_estado == 'confirmada':
            enviar_confirmacion_reserva(
                email_cliente=reserva.cliente.email,
                nombre_cliente=reserva.cliente.first_name or reserva.cliente.username,
                numero_reserva=reserva.id,
                habitacion_numero=reserva.habitacion.numero,
                fecha_entrada=reserva.fecha_entrada,
                fecha_salida=reserva.fecha_salida,
                precio_total=reserva.precio_total
            )

        messages.success(
            request,
            f'Estado de reserva #{reserva.id} cambiado de "{reserva.get_estado_display()}" '
            f'a "{dict(reserva.ESTADOS_RESERVA)[nuevo_estado]}".'
        )
    else:
        messages.error(request, 'Estado de reserva inválido.')

    return redirect('gestionar_reservas')


@user_passes_test(es_administrador)
def cambiar_estado_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    nuevo_estado = request.POST.get('nuevo_estado')

    if nuevo_estado in ['disponible', 'ocupada', 'mantenimiento']:
        estado_anterior = habitacion.estado
        habitacion.estado = nuevo_estado
        habitacion.save()

        if nuevo_estado == 'disponible':
            reservas_activas = habitacion.reservas.filter(
                estado__in=['pendiente', 'confirmada'],
                fecha_salida__gte=date.today()
            )
            if reservas_activas.exists():
                messages.warning(request,
                    f'Habitación {habitacion.numero} marcada como disponible, pero tiene {reservas_activas.count()} reservas activas. '
                    'Considera cancelar las reservas si es necesario.')

        messages.success(request, f'Estado de habitación {habitacion.numero} cambiado a {habitacion.get_estado_display()}.')
    else:
        messages.error(request, 'Estado de habitación inválido.')

    return redirect('lista_habitaciones')


@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(cliente=request.user).order_by('-fecha_reserva')
    return render(request, 'hotel/mis_reservas.html', {'reservas': reservas})


@user_passes_test(es_administrador)
def gestionar_reservas(request):
    reservas = Reserva.objects.all().order_by('-fecha_reserva')

    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        reservas = reservas.filter(estado=estado_filtro)

    contexto = {
        'reservas': reservas,
        'estado_seleccionado': estado_filtro,
    }
    return render(request, 'hotel/gestionar_reservas.html', contexto)


@user_passes_test(es_administrador)
def agregar_habitacion(request):
    if request.method == 'POST':
        form = HabitacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habitación agregada exitosamente.')
            return redirect('lista_habitaciones')
    else:
        form = HabitacionForm()

    return render(request, 'hotel/agregar_habitacion.html', {'form': form})


def registrarse(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()

            # Crear perfil del usuario con los datos adicionales
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=usuario)
            if 'telefono' in form.cleaned_data:
                perfil.telefono = form.cleaned_data.get('telefono', '')
            if 'direccion' in form.cleaned_data:
                perfil.direccion = form.cleaned_data.get('direccion', '')
            perfil.save()

            # Enviar email de bienvenida
            try:
                nombre_completo = f"{usuario.first_name} {usuario.last_name}"
                asunto = "Bienvenido a Hotel Manager"
                mensaje = f"""Hola {nombre_completo},

Tu cuenta ha sido creada exitosamente.

Nombre de usuario: {usuario.username}
Correo: {usuario.email}

Ya puedes iniciar sesión y comenzar a hacer reservas.

¡Bienvenido a Hotel Manager!"""

                send_mail(
                    asunto,
                    mensaje,
                    None,
                    [usuario.email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Error al enviar email: {e}")

            username = form.cleaned_data.get('username')
            messages.success(request, f'Cuenta creada para {username}! Te hemos enviado un correo de bienvenida.')
            return redirect('iniciar_sesion')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registrarse.html', {'form': form})