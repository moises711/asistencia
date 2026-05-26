from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Justificacion, RegistroAsistencia


@receiver(post_save, sender=RegistroAsistencia)
def notificar_tardanza(sender, instance: RegistroAsistencia, created: bool, **kwargs):
    if instance.estado != RegistroAsistencia.ESTADO_TARDANZA:
        return
    supervisor = getattr(instance.empleado, "supervisor", None)
    if not supervisor or not supervisor.email:
        return
    asunto = "Alerta de tardanza"
    mensaje = f"El empleado {instance.empleado.username} registro tardanza el {instance.fecha}."
    send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [supervisor.email], fail_silently=True)


@receiver(post_save, sender=Justificacion)
def notificar_justificacion(sender, instance: Justificacion, created: bool, **kwargs):
    if not created:
        return
    supervisor = getattr(instance.asistencia.empleado, "supervisor", None)
    if not supervisor or not supervisor.email:
        return
    asunto = "Nueva solicitud de justificacion"
    mensaje = f"El empleado {instance.asistencia.empleado.username} envio una justificacion."
    send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, [supervisor.email], fail_silently=True)
