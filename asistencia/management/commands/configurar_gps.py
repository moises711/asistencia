from django.core.management.base import BaseCommand
from asistencia.models import ConfiguracionGPS


class Command(BaseCommand):
    help = 'Configura las coordenadas GPS de la oficina'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre',
            type=str,
            default='Oficina Principal',
            help='Nombre de la oficina'
        )
        parser.add_argument(
            '--latitud',
            type=float,
            required=True,
            help='Latitud de la oficina'
        )
        parser.add_argument(
            '--longitud',
            type=float,
            required=True,
            help='Longitud de la oficina'
        )
        parser.add_argument(
            '--radio',
            type=int,
            default=500,
            help='Radio permitido en metros (default: 500)'
        )

    def handle(self, *args, **options):
        nombre = options['nombre']
        latitud = options['latitud']
        longitud = options['longitud']
        radio = options['radio']

        # Desactivar configuraciones anteriores
        ConfiguracionGPS.objects.filter(activa=True).update(activa=False)

        # Crear o actualizar
        config, created = ConfiguracionGPS.objects.get_or_create(
            nombre=nombre,
            defaults={
                'latitud': latitud,
                'longitud': longitud,
                'radio_permitido_metros': radio,
                'activa': True
            }
        )

        if not created:
            config.latitud = latitud
            config.longitud = longitud
            config.radio_permitido_metros = radio
            config.activa = True
            config.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Configuración GPS creada/actualizada:\n'
                f'  - Nombre: {nombre}\n'
                f'  - Latitud: {latitud}\n'
                f'  - Longitud: {longitud}\n'
                f'  - Radio: {radio}m'
            )
        )
