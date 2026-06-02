from django.core.management.base import BaseCommand
from django.utils import timezone

from asistencia.models import AusenciaProgramada, CustomUser, DiaFeriado, RegistroAsistencia, RecuperacionDia


class Command(BaseCommand):
    help = "Genera registros de falta para empleados sin marcacion del dia."

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        if DiaFeriado.objects.filter(fecha=hoy).exists():
            self.stdout.write(self.style.WARNING("Dia feriado, no se generan faltas."))
            return

        empleados = CustomUser.objects.filter(rol=CustomUser.ROL_EMPLEADO, is_active=True)
        faltas_creadas = 0

        for empleado in empleados:
            # Saltar si no es laborable según su horario
            if empleado.horario and not empleado.horario.es_laborable(hoy):
                continue

            # Saltar si tiene permiso/ausencia aprobada para hoy
            if AusenciaProgramada.objects.filter(
                empleado=empleado,
                estado=AusenciaProgramada.ESTADO_APROBADA,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy,
            ).exists():
                continue

            # Revisar si ya existe un registro de asistencia para hoy
            registro = RegistroAsistencia.objects.filter(empleado=empleado, fecha=hoy).first()

            if registro:
                # Si existe pero no tiene hora de entrada y no es permiso/recuperacion, marcar como falta
                if not registro.hora_entrada and registro.estado not in (
                    RegistroAsistencia.ESTADO_PERMISO,
                    RegistroAsistencia.ESTADO_RECUPERACION,
                ):
                    registro.estado = RegistroAsistencia.ESTADO_FALTA
                    registro.save(update_fields=["estado"])

                    if empleado.horario:
                        RecuperacionDia.objects.get_or_create(
                            empleado=empleado,
                            fecha_falta=hoy,
                            defaults={
                                'horas_a_recuperar': empleado.horario.duracion_jornada(),
                                'registro_falta': registro,
                            }
                        )
                    faltas_creadas += 1
                # Si ya tiene entrada, no hacer nada
                continue

            # No existe registro: crear falta automática
            registro_falta = RegistroAsistencia.objects.create(
                empleado=empleado,
                fecha=hoy,
                estado=RegistroAsistencia.ESTADO_FALTA,
            )
            if empleado.horario:
                RecuperacionDia.objects.get_or_create(
                    empleado=empleado,
                    fecha_falta=hoy,
                    defaults={
                        'horas_a_recuperar': empleado.horario.duracion_jornada(),
                        'registro_falta': registro_falta,
                    }
                )
            faltas_creadas += 1

        self.stdout.write(self.style.SUCCESS(f"Faltas creadas: {faltas_creadas}"))
