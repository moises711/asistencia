from datetime import datetime, timedelta
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class ConfiguracionGPS(models.Model):
    """Configuración de ubicación GPS de la oficina"""
    nombre = models.CharField(max_length=100, default="Oficina Principal")
    latitud = models.DecimalField(max_digits=9, decimal_places=6, help_text="Latitud de la oficina")
    longitud = models.DecimalField(max_digits=9, decimal_places=6, help_text="Longitud de la oficina")
    radio_permitido_metros = models.IntegerField(default=20, help_text="Radio permitido en metros para marcar asistencia")
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración GPS"
        verbose_name_plural = "Configuraciones GPS"

    def __str__(self):
        return f"{self.nombre} ({self.latitud}, {self.longitud})"

    @classmethod
    def obtener_configuracion_activa(cls):
        """Obtiene la configuración GPS activa"""
        return cls.objects.filter(activa=True).first()


class Area(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej. Diseño Gráfico, Ing. Software")
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Horario(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej. Turno Mañana")
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    tolerancia_minutos = models.IntegerField(default=0)
    
    # Días laborables
    lunes = models.BooleanField(default=True)
    martes = models.BooleanField(default=True)
    miercoles = models.BooleanField(default=True)
    jueves = models.BooleanField(default=True)
    viernes = models.BooleanField(default=True)
    sabado = models.BooleanField(default=False)
    domingo = models.BooleanField(default=False)

    def hora_entrada_con_tolerancia(self):
        return (timezone.datetime.combine(timezone.localdate(), self.hora_entrada) + timedelta(minutes=self.tolerancia_minutos)).time()

    def es_laborable(self, fecha):
        dia = fecha.weekday()
        if dia == 0:
            return self.lunes
        if dia == 1:
            return self.martes
        if dia == 2:
            return self.miercoles
        if dia == 3:
            return self.jueves
        if dia == 4:
            return self.viernes
        if dia == 5:
            return self.sabado
        return self.domingo

    def duracion_jornada(self):
        entrada = datetime.combine(timezone.localdate(), self.hora_entrada)
        salida = datetime.combine(timezone.localdate(), self.hora_salida)
        if salida <= entrada:
            salida += timedelta(days=1)
        return salida - entrada

    def __str__(self):
        return f"{self.nombre} ({self.hora_entrada} - {self.hora_salida})"


class CustomUser(AbstractUser):
    ROL_ADMIN = "admin"
    ROL_RRHH = "rrhh"
    ROL_SUPERVISOR = "supervisor"
    ROL_EMPLEADO = "empleado"

    ROLES = (
        (ROL_ADMIN, "Administrador"),
        (ROL_RRHH, "RRHH"),
        (ROL_SUPERVISOR, "Supervisor"),
        (ROL_EMPLEADO, "Empleado"),
    )
    
    rol = models.CharField(max_length=20, choices=ROLES, default=ROL_EMPLEADO)
    dni = models.CharField(max_length=11, unique=True, verbose_name="DNI/CE")
    supervisor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subordinados'
    )
    horario = models.ForeignKey(
        Horario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='empleados'
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empleados',
        verbose_name="Área de Práctica"
    )
    permite_remoto = models.BooleanField(default=False)
    codigo_qr = models.CharField(
        max_length=50, 
        unique=True, 
        editable=False,
        null=True,
        blank=True,
        help_text="Código QR único del empleado para validar asistencia"
    )

    def save(self, *args, **kwargs):
        # Generar código QR único si no existe
        if not self.codigo_qr:
            # Usar UUID acortado + últimos 4 dígitos del DNI
            codigo_base = str(uuid.uuid4())[:8].upper()
            dni_parte = self.dni[-4:] if len(self.dni) >= 4 else self.dni
            self.codigo_qr = f"{codigo_base}-{dni_parte}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.dni}) - {self.area.nombre if self.area else 'Sin Área'}"


class IpOficinaAutorizada(models.Model):
    nombre_sede = models.CharField(max_length=120)
    ip_publica = models.GenericIPAddressField(protocol="IPv4")
    activa = models.BooleanField(default=True)

    def __str__(self):
        estado = "Activa" if self.activa else "Inactiva"
        return f"{self.nombre_sede} - {self.ip_publica} ({estado})"


class RegistroAsistencia(models.Model):
    ESTADO_A_TIEMPO = "a_tiempo"
    ESTADO_TARDANZA = "tardanza"
    ESTADO_FALTA = "falta"
    ESTADO_PERMISO = "permiso"
    ESTADO_RECUPERACION = "recuperacion"

    ESTADOS = (
        (ESTADO_A_TIEMPO, "A tiempo"),
        (ESTADO_TARDANZA, "Tardanza"),
        (ESTADO_FALTA, "Falta"),
        (ESTADO_PERMISO, "Permiso"),
        (ESTADO_RECUPERACION, "Recuperación"),
    )

    empleado = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="registros")
    fecha = models.DateField()
    hora_entrada = models.DateTimeField(null=True, blank=True)
    hora_salida = models.DateTimeField(null=True, blank=True)
    inicio_almuerzo = models.DateTimeField(null=True, blank=True)
    fin_almuerzo = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_A_TIEMPO)
    ip_registro = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    # Campos para validación GPS
    latitud_entrada = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud_entrada = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    latitud_salida = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud_salida = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    precisión_entrada = models.FloatField(null=True, blank=True, help_text="Precisión GPS en metros")
    precisión_salida = models.FloatField(null=True, blank=True, help_text="Precisión GPS en metros")
    horas_netas_trabajadas = models.DurationField(null=True, blank=True)
    actividad_diaria = models.TextField(null=True, blank=True, help_text="Resumen de lo que hizo el practicante hoy.")

    class Meta:
        unique_together = ("empleado", "fecha")
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.empleado.username} - {self.fecha}"


class Justificacion(models.Model):
    asistencia = models.ForeignKey(RegistroAsistencia, on_delete=models.CASCADE, related_name="justificaciones")
    motivo = models.TextField()
    aprobada = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Justificacion {self.asistencia.empleado.username} - {self.asistencia.fecha}"


class AusenciaProgramada(models.Model):
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_APROBADA = "aprobada"
    ESTADO_RECHAZADA = "rechazada"

    ESTADOS_PERMISO = (
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_APROBADA, "Aprobada"),
        (ESTADO_RECHAZADA, "Rechazada"),
    )

    empleado = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="ausencias_programadas")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADOS_PERMISO, default=ESTADO_PENDIENTE)
    creada_en = models.DateTimeField(auto_now_add=True)
    creada_por = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ausencias_creadas",
    )
    procesada_por = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="permisos_procesados"
    )

    @property
    def aprobada(self):
        """Backward compatibility property."""
        return self.estado == self.ESTADO_APROBADA

    def __str__(self):
        return f"{self.empleado.username} ({self.fecha_inicio} - {self.fecha_fin}) [{self.get_estado_display()}]"


class MetaHorasPracticante(models.Model):
    """Meta total de horas de práctica que debe cumplir un practicante."""
    empleado = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="meta_horas")
    horas_totales_requeridas = models.IntegerField(default=300, help_text="Total de horas de práctica requeridas")
    fecha_inicio_practica = models.DateField()
    fecha_fin_practica = models.DateField()

    class Meta:
        verbose_name = "Meta de Horas"
        verbose_name_plural = "Metas de Horas"

    def __str__(self):
        return f"{self.empleado.username} - {self.horas_totales_requeridas}h"


class RecuperacionDia(models.Model):
    """Deuda de horas por falta sin permiso que debe recuperarse (típicamente sábados)."""
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_RECUPERADO = "recuperado"
    ESTADO_EXCLUIDO = "excluido"

    ESTADOS_RECUPERACION = (
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_RECUPERADO, "Recuperado"),
        (ESTADO_EXCLUIDO, "Excluido"),
    )

    empleado = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="recuperaciones")
    fecha_falta = models.DateField(help_text="Día que faltó")
    registro_falta = models.OneToOneField(
        RegistroAsistencia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recuperacion",
        help_text="Falta original asociada a esta recuperación.",
    )
    horas_a_recuperar = models.DurationField(help_text="Horas que debe recuperar")
    fecha_recuperacion = models.DateField(null=True, blank=True, help_text="Sábado en que recuperó")
    horas_recuperadas = models.DurationField(default=timedelta(0))
    estado = models.CharField(max_length=20, choices=ESTADOS_RECUPERACION, default=ESTADO_PENDIENTE)
    motivo_exclusion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Recuperación de Día"
        verbose_name_plural = "Recuperaciones de Días"
        ordering = ["-fecha_falta"]

    def __str__(self):
        return f"{self.empleado.username} - Falta {self.fecha_falta} [{self.get_estado_display()}]"


class DiaFeriado(models.Model):
    fecha = models.DateField(unique=True)
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.fecha} - {self.descripcion}"