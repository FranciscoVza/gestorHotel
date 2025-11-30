from django.core.mail import send_mail
from django.conf import settings

def enviar_confirmacion_reserva(email_cliente, nombre_cliente, numero_reserva, habitacion_numero=None, fecha_entrada=None, fecha_salida=None, precio_total=None):
    """
    Envía un email de confirmación de reserva al cliente
    """
    asunto = f"Confirmación de Reserva #{numero_reserva} - Hotel Manager"

    # Construir el mensaje
    mensaje = f"""Hola {nombre_cliente},

Tu reserva ha sido CONFIRMADA exitosamente.

═══════════════════════════════════════════
DETALLES DE TU RESERVA
═══════════════════════════════════════════
Número de Reserva: {numero_reserva}"""

    if habitacion_numero:
        mensaje += f"\nHabitación: {habitacion_numero}"

    if fecha_entrada:
        mensaje += f"\nFecha de Entrada: {fecha_entrada}"

    if fecha_salida:
        mensaje += f"\nFecha de Salida: {fecha_salida}"

    if precio_total:
        mensaje += f"\nPrecio Total: ${precio_total}"

    mensaje += """

═══════════════════════════════════════════

Gracias por preferir Hotel Manager.
Si tienes alguna pregunta, no dudes en contactarnos.

¡Que disfrutes tu estadía!

Hotel Manager
"""

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email_cliente],
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Error al enviar email de confirmación: {e}")
        return False

