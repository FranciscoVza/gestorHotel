from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
from .models import Habitacion, Reserva, TipoHabitacion, PerfilUsuario
from .forms import ReservaForm, HabitacionForm, TipoHabitacionForm

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
    }
    return render(request, 'hotel/inicio.html', contexto)

def actualizar_reservas_vencidas():
    ahora = timezone.now()
    vencidas = Reserva.objects.filter(fecha_salida__lt=ahora, estado="confirmada")

    for r in vencidas:
        r.estado = "completada"
        r.habitacion.disponible = True
        r.habitacion.save()
        r.save()

def lista_habitaciones(request):
    #actualizamos las reservas vencidas antes de mostrar
    actualizar_reservas_vencidas()

    habitaciones = Habitacion.objects.all()
    return render(request, "hotel/habitaciones.html", {"habitaciones": habitaciones})


def lista_habitaciones(request):
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

    # Nuevo filtro por disponibilidad real
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

@login_required
def hacer_reserva(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)

    # Verificar disponibilidad real (no solo el estado)
    if not habitacion.esta_disponible():
        messages.error(request, 'Esta habitación no está disponible para reservas. Tiene reservas pendientes o confirmadas.')
        return redirect('lista_habitaciones')

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.cliente = request.user
            reserva.habitacion = habitacion

            # Validar fechas
            if reserva.fecha_entrada < date.today():
                messages.error(request, 'La fecha de entrada no puede ser anterior a hoy.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas()
                })

            if reserva.fecha_salida <= reserva.fecha_entrada:
                messages.error(request, 'La fecha de salida debe ser posterior a la fecha de entrada.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas()
                })

            # Verificar disponibilidad para las fechas específicas
            if not habitacion.esta_disponible(reserva.fecha_entrada, reserva.fecha_salida):
                messages.error(request, 'La habitación no está disponible para las fechas seleccionadas. Hay conflictos con otras reservas.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas()
                })

            # Validar capacidad
            if reserva.numero_huespedes > habitacion.tipo.capacidad_maxima:
                messages.error(request, f'Esta habitación tiene capacidad máxima para {habitacion.tipo.capacidad_maxima} huéspedes.')
                return render(request, 'hotel/hacer_reserva.html', {
                    'form': form,
                    'habitacion': habitacion,
                    'proximas_reservas': habitacion.proximas_reservas()
                })

            reserva.save()  # Esto automáticamente actualizará el estado de la habitación
            messages.success(request, '¡Reserva realizada exitosamente! Tu reserva está pendiente de confirmación.')
            return redirect('mis_reservas')
    else:
        form = ReservaForm()

    contexto = {
        'form': form,
        'habitacion': habitacion,
        'proximas_reservas': habitacion.proximas_reservas()
    }
    return render(request, 'hotel/hacer_reserva.html', contexto)

@user_passes_test(es_administrador)
def cambiar_estado_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    nuevo_estado = request.POST.get('nuevo_estado')

    if nuevo_estado in ['pendiente', 'confirmada', 'cancelada', 'completada']:
        estado_anterior = reserva.estado
        reserva.estado = nuevo_estado
        reserva.save()  # Esto automaticamente actualizara el estado de la habitacion

        messages.success(request, f'Estado de reserva #{reserva.id} cambiado de "{reserva.get_estado_display()}" a "{dict(reserva.ESTADOS_RESERVA)[nuevo_estado]}".')
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

        # Si se marca como disponible, verificar que no tenga reservas activas
        if nuevo_estado == 'disponible':
            reservas_activas = habitacion.reserva_set.filter(
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

    # Filtros para admin
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
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            PerfilUsuario.objects.create(usuario=usuario)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Cuenta creada para {username}!')
            return redirect('iniciar_sesion')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registrarse.html', {'form': form})