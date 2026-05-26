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
            if empleado.horario and not empleado.horario.es_laborable(hoy):
                continue
            if AusenciaProgramada.objects.filter(
                empleado=empleado,
                estado=AusenciaProgramada.ESTADO_APROBADA,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy,
            ).exists():
                continue
            if RegistroAsistencia.objects.filter(empleado=empleado, fecha=hoy).exists():
                continue
            RegistroAsistencia.objects.create(
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
                    }
                )
            faltas_creadas += 1

        self.stdout.write(self.style.SUCCESS(f"Faltas creadas: {faltas_creadas}"))
