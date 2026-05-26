"""
Ejemplos avanzados para la validación GPS de asistencia
"""

from django.db.models import Q
from asistencia.models import RegistroAsistencia, ConfiguracionGPS
from asistencia.utils import calcular_distancia_gps


# ============================================================================
# EJEMPLOS DE CONSULTAS
# ============================================================================

def obtener_asistencias_con_gps_valido(fecha=None):
    """Obtener registros de asistencia que fueron marcados con GPS válido"""
    query = RegistroAsistencia.objects.filter(
        latitud_entrada__isnull=False,
        longitud_entrada__isnull=False
    )
    if fecha:
        query = query.filter(fecha=fecha)
    return query


def obtener_asistencias_sin_gps(fecha=None):
    """Obtener registros sin validación GPS"""
    query = RegistroAsistencia.objects.filter(
        Q(latitud_entrada__isnull=True) | Q(longitud_entrada__isnull=True)
    )
    if fecha:
        query = query.filter(fecha=fecha)
    return query


def obtener_asistencias_remotas(fecha=None):
    """
    Obtener asistencias que se registraron desde fuera del radio permitido.
    Requiere que el sistema haya validado y guardado como remota.
    """
    config = ConfiguracionGPS.obtener_configuracion_activa()
    if not config:
        return RegistroAsistencia.objects.none()
    
    registros = obtener_asistencias_con_gps_valido(fecha)
    remotas = []
    
    for registro in registros:
        distancia = calcular_distancia_gps(
            registro.latitud_entrada,
            registro.longitud_entrada,
            config.latitud,
            config.longitud
        )
        if distancia > config.radio_permitido_metros:
            remotas.append({
                'registro': registro,
                'distancia': distancia
            })
    
    return remotas


# ============================================================================
# EJEMPLOS DE REPORTES
# ============================================================================

def generar_reporte_gps_por_empleado(empleado, fecha_inicio=None, fecha_fin=None):
    """
    Genera reporte de ubicación GPS por empleado
    """
    query = RegistroAsistencia.objects.filter(empleado=empleado)
    
    if fecha_inicio:
        query = query.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        query = query.filter(fecha__lte=fecha_fin)
    
    config = ConfiguracionGPS.obtener_configuracion_activa()
    
    reporte = {
        'empleado': empleado,
        'total_registros': query.count(),
        'con_gps': query.filter(
            latitud_entrada__isnull=False
        ).count(),
        'sin_gps': query.filter(
            latitud_entrada__isnull=True
        ).count(),
        'registros_detalle': []
    }
    
    for registro in query:
        if registro.latitud_entrada and config:
            distancia = calcular_distancia_gps(
                registro.latitud_entrada,
                registro.longitud_entrada,
                config.latitud,
                config.longitud
            )
        else:
            distancia = None
        
        reporte['registros_detalle'].append({
            'fecha': registro.fecha,
            'entrada': registro.hora_entrada,
            'latitud': float(registro.latitud_entrada) if registro.latitud_entrada else None,
            'longitud': float(registro.longitud_entrada) if registro.longitud_entrada else None,
            'distancia': round(distancia, 2) if distancia else None,
            'precision': registro.precisión_entrada,
            'valido': distancia <= config.radio_permitido_metros if distancia and config else None
        })
    
    return reporte


def generar_reporte_cumplimiento_gps(fecha):
    """
    Reporte de cumplimiento de validación GPS en una fecha
    """
    registros = RegistroAsistencia.objects.filter(fecha=fecha)
    config = ConfiguracionGPS.obtener_configuracion_activa()
    
    if not config:
        return {
            'error': 'Configuración GPS no disponible',
            'config_gps': None
        }
    
    estadisticas = {
        'fecha': fecha,
        'total_registros': registros.count(),
        'con_gps': 0,
        'sin_gps': 0,
        'dentro_rango': 0,
        'fuera_rango': 0,
        'empleados_remotos': [],
        'config_gps': {
            'latitud': float(config.latitud),
            'longitud': float(config.longitud),
            'radio_permitido': config.radio_permitido_metros
        }
    }
    
    for registro in registros:
        if registro.latitud_entrada:
            estadisticas['con_gps'] += 1
            
            distancia = calcular_distancia_gps(
                registro.latitud_entrada,
                registro.longitud_entrada,
                config.latitud,
                config.longitud
            )
            
            if distancia <= config.radio_permitido_metros:
                estadisticas['dentro_rango'] += 1
            else:
                estadisticas['fuera_rango'] += 1
                estadisticas['empleados_remotos'].append({
                    'empleado': str(registro.empleado),
                    'distancia': round(distancia, 2),
                    'hora_entrada': registro.hora_entrada
                })
        else:
            estadisticas['sin_gps'] += 1
    
    return estadisticas


# ============================================================================
# EJEMPLOS DE VALIDACIONES AVANZADAS
# ============================================================================

def validar_gps_requerido(registro):
    """
    Valida que un registro haya sido marcado con GPS
    Útil si GPS es requerido
    """
    return {
        'tiene_entrada_gps': registro.latitud_entrada is not None,
        'tiene_salida_gps': registro.latitud_salida is not None,
        'ambas_validas': (registro.latitud_entrada is not None and 
                         registro.latitud_salida is not None),
        'precision_entrada_buena': registro.precisión_entrada and registro.precisión_entrada < 20,
        'precision_salida_buena': registro.precisión_salida and registro.precisión_salida < 20,
    }


def calcular_trayecto(registro):
    """
    Calcula la trayectoria entre entrada y salida
    """
    if not all([registro.latitud_entrada, registro.longitud_entrada,
                registro.latitud_salida, registro.longitud_salida]):
        return None
    
    distancia = calcular_distancia_gps(
        registro.latitud_entrada,
        registro.longitud_entrada,
        registro.latitud_salida,
        registro.longitud_salida
    )
    
    return {
        'punto_entrada': {
            'latitud': float(registro.latitud_entrada),
            'longitud': float(registro.longitud_entrada),
        },
        'punto_salida': {
            'latitud': float(registro.latitud_salida),
            'longitud': float(registro.longitud_salida),
        },
        'distancia_recorrida': round(distancia, 2),
    }


# ============================================================================
# EJEMPLOS DE USO EN VISTAS
# ============================================================================

def vista_ejemplo_reporte_gps(request):
    """Ejemplo de vista que muestra un reporte GPS"""
    from django.shortcuts import render
    from django.utils import timezone
    
    fecha = request.GET.get('fecha', timezone.localdate())
    reporte = generar_reporte_cumplimiento_gps(fecha)
    
    return render(request, 'reporte_gps.html', {'reporte': reporte})


def vista_ejemplo_detector_remoto(request):
    """
    Detecta empleados que marcaron desde fuera del rango
    y envía alertas
    """
    from django.utils import timezone
    
    fecha = timezone.localdate()
    remotas = obtener_asistencias_remotas(fecha)
    
    for item in remotas:
        registro = item['registro']
        distancia = item['distancia']
        
        # Aquí podrías enviar alertas, crear notificaciones, etc.
        print(f"⚠️  {registro.empleado} marcó desde {distancia}m")
        
        # Ejemplo: Crear una justificación automática
        # justificacion = Justificacion.objects.create(
        #     asistencia=registro,
        #     motivo=f"Marcación remota: {distancia}m de la oficina",
        #     aprobada=False
        # )


# ============================================================================
# COMANDOS DE SHELL
# ============================================================================

"""
# Ver todos los registros con GPS
from asistencia.models import RegistroAsistencia
RegistroAsistencia.objects.filter(latitud_entrada__isnull=False).values(
    'empleado', 'fecha', 'latitud_entrada', 'longitud_entrada'
)

# Contar registros por tipo
from django.db.models import Count
RegistroAsistencia.objects.values('empleado').annotate(
    total=Count('id'),
    con_gps=Count('latitud_entrada')
)

# Generar reporte para un empleado
from django.contrib.auth import get_user_model
from ejemplos import generar_reporte_gps_por_empleado
User = get_user_model()
empleado = User.objects.first()
reporte = generar_reporte_gps_por_empleado(empleado)
print(reporte)
"""
