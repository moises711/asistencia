#!/usr/bin/env python
"""
=================================================================
    SISTEMA DE VALIDACIÓN GPS PARA CONTROL DE ASISTENCIA
=================================================================

DESCRIPCIÓN:
Sistema completo que captura coordenadas GPS de los empleados
para validar que marquen asistencia desde la ubicación correcta
(la oficina).

IMPLEMENTACIÓN COMPLETADA: ✅
=================================================================
"""

# ============================================================================
# 1. INSTALACIÓN Y CONFIGURACIÓN
# ============================================================================

"""
PASO 1: Las migraciones ya están aplicadas
    ✅ python manage.py migrate asistencia
    ✅ Se creó modelo ConfiguracionGPS
    ✅ Se actualizó RegistroAsistencia con 6 campos GPS

PASO 2: Configurar ubicación de la oficina
    python manage.py configurar_gps \
        --latitud 10.5123456 \
        --longitud -75.3456789 \
        --radio 500 \
        --nombre "Oficina Principal"

PASO 3: Verificar configuración
    python manage.py shell
    >>> from asistencia.models import ConfiguracionGPS
    >>> ConfiguracionGPS.obtener_configuracion_activa()
    <ConfiguracionGPS: Oficina Principal (10.512346, -75.345679)>

PASO 4: ¡Listo! Los usuarios pueden usar GPS en el dashboard
"""

# ============================================================================
# 2. FLUJO DE USUARIO EN EL DASHBOARD
# ============================================================================

"""
FLUJO VISUAL:
1. Usuario abre Dashboard
2. Ve botón "📍 Ubicación GPS" con estado
   - Pendiente (gris)
   - Calculando... (amarillo)
   - ✓ En la oficina 145m (verde)
   - ✗ Fuera de rango 2500m (rojo)

3. Usuario hace click en "Ubicación GPS"
   - Navegador pide permiso para GPS
   - Usuario acepta
   - Se capturan coordenadas

4. Sistema valida con servidor (/validar-gps/)
   - Calcula distancia a la oficina
   - Compara con radio permitido
   - Actualiza estado

5. Usuario marca entrada/salida
   - Se envían coordenadas GPS
   - Se guardan en BD automáticamente
   - Fin del proceso

TIEMPO TOTAL: ~2-5 segundos
"""

# ============================================================================
# 3. ARCHIVOS MODIFICADOS Y CREADOS
# ============================================================================

"""
ARCHIVOS MODIFICADOS:
  ✏️ asistencia/models.py
     - Nuevo modelo: ConfiguracionGPS
     - Actualizado: RegistroAsistencia (+6 campos GPS)
  
  ✏️ asistencia/utils.py
     - Nueva función: calcular_distancia_gps()
     - Nueva función: validar_ubicacion_gps()
  
  ✏️ asistencia/views.py
     - Nueva vista: validar_gps() [POST /validar-gps/]
     - Actualizada: marcar_evento() [guarda GPS]
  
  ✏️ asistencia/urls.py
     - Nueva ruta: path('validar-gps/', ...)
  
  ✏️ asistencia/templates/asistencia/dashboard.html
     - Actualizada función: solicitarGPS()
     - Actualizada integración con botones

ARCHIVOS CREADOS:
  ✨ asistencia/management/commands/configurar_gps.py
     - Comando CLI para configurar GPS
  
  ✨ asistencia/documentacion/gps-validacion.md
     - Documentación técnica completa
  
  ✨ asistencia/ejemplos_gps.py
     - Ejemplos avanzados de uso
  
  ✨ asistencia/migrations/0003_configuraciongps_registroasistencia_*.py
     - Migraciones (aplicadas)
  
  📚 GPS_README.md
     - Guía rápida de inicio
  
  📚 GPS_VISUAL_GUIDE.md
     - Diagramas y ejemplos visuales
"""

# ============================================================================
# 4. API ENDPOINT
# ============================================================================

"""
POST /validar-gps/

Valida las coordenadas GPS del usuario

REQUEST (JSON):
{
    "latitud": 10.5123456,
    "longitud": -75.3456789,
    "precisión": 5.5
}

RESPONSE (válido):
{
    "valido": true,
    "distancia": 145.32,
    "mensaje": "Distancia: 145.32m - Ubicación válida",
    "precision": 5.5,
    "radio_permitido": 500
}

RESPONSE (no válido):
{
    "valido": false,
    "distancia": 2500.50,
    "mensaje": "Distancia: 2500.50m - Fuera del rango permitido",
    "precision": 6.2,
    "radio_permitido": 500
}

RESPONSE (error):
{
    "valido": false,
    "mensaje": "Configuración de ubicación de oficina no disponible"
}
"""

# ============================================================================
# 5. EJEMPLOS DE USO DESDE PYTHON
# ============================================================================

"""
# Ver todos los registros con GPS
from asistencia.models import RegistroAsistencia
registros_con_gps = RegistroAsistencia.objects.filter(
    latitud_entrada__isnull=False
)
print(f"Total con GPS: {registros_con_gps.count()}")

# Ver registros sin GPS
registros_sin_gps = RegistroAsistencia.objects.filter(
    latitud_entrada__isnull=True
)
print(f"Total sin GPS: {registros_sin_gps.count()}")

# Validar ubicación de un registro
from asistencia.utils import validar_ubicacion_gps
from asistencia.models import ConfiguracionGPS

registro = RegistroAsistencia.objects.first()
config = ConfiguracionGPS.obtener_configuracion_activa()

if registro.latitud_entrada:
    resultado = validar_ubicacion_gps(
        registro.latitud_entrada,
        registro.longitud_entrada,
        config.latitud,
        config.longitud,
        config.radio_permitido_metros
    )
    print(resultado)
    # {'valido': True, 'distancia': 145.32, 'mensaje': '...'}

# Generar reporte por empleado
from asistencia.ejemplos_gps import generar_reporte_gps_por_empleado
empleado = CustomUser.objects.first()
reporte = generar_reporte_gps_por_empleado(empleado)
print(f"Total registros: {reporte['total_registros']}")
print(f"Con GPS: {reporte['con_gps']}")

# Generar reporte de cumplimiento
from asistencia.ejemplos_gps import generar_reporte_cumplimiento_gps
from django.utils import timezone
reporte = generar_reporte_cumplimiento_gps(timezone.localdate())
print(f"Total: {reporte['total_registros']}")
print(f"Dentro de rango: {reporte['dentro_rango']}")
print(f"Fuera de rango: {reporte['fuera_rango']}")
if reporte['empleados_remotos']:
    for emp in reporte['empleados_remotos']:
        print(f"  - {emp['empleado']}: {emp['distancia']}m")
"""

# ============================================================================
# 6. CONSULTAS SQL ÚTILES
# ============================================================================

"""
-- Ver todos los registros con GPS
SELECT empleado_id, fecha, latitud_entrada, longitud_entrada, 
       precisión_entrada, hora_entrada
FROM asistencia_registroasistencia
WHERE latitud_entrada IS NOT NULL;

-- Contar registros por tipo
SELECT COUNT(*) as total, 
       COUNT(CASE WHEN latitud_entrada IS NOT NULL THEN 1 END) as con_gps,
       COUNT(CASE WHEN latitud_entrada IS NULL THEN 1 END) as sin_gps
FROM asistencia_registroasistencia;

-- Ver empleados que marcaron desde múltiples ubicaciones
SELECT empleado_id, COUNT(DISTINCT latitud_entrada) as ubicaciones_unicas
FROM asistencia_registroasistencia
WHERE latitud_entrada IS NOT NULL
GROUP BY empleado_id
HAVING COUNT(DISTINCT latitud_entrada) > 3;
"""

# ============================================================================
# 7. CONFIGURACIÓN AVANZADA
# ============================================================================

"""
# Hacer GPS obligatorio (opcional)
# En views.py, dentro de marcar_evento(), agregar:

if accion == "entrada":
    # Obtener config
    config_gps = ConfiguracionGPS.obtener_configuracion_activa()
    
    # Obtener coordenadas enviadas
    latitud = request.POST.get('latitud')
    longitud = request.POST.get('longitud')
    
    # Validar GPS
    if not latitud or not longitud:
        return JsonResponse({
            'status': 'error',
            'message': 'GPS es requerido para marcar entrada'
        }, status=403)
    
    # Validar que esté en rango
    from asistencia.utils import validar_ubicacion_gps
    resultado = validar_ubicacion_gps(
        latitud, longitud,
        config_gps.latitud, config_gps.longitud,
        config_gps.radio_permitido_metros
    )
    
    if not resultado['valido']:
        return JsonResponse({
            'status': 'error',
            'message': f"Debes estar en la oficina. {resultado['mensaje']}"
        }, status=403)
    
    # Continuar con el registro normal
    ...
"""

# ============================================================================
# 8. SOLUCIÓN DE PROBLEMAS
# ============================================================================

"""
PROBLEMA: "Error - Configuración GPS no disponible"
CAUSA: No se configuró ConfiguracionGPS
SOLUCIÓN: 
    python manage.py configurar_gps --latitud X --longitud Y

PROBLEMA: "No se pudo obtener la ubicación"
CAUSA: 
    - Usuario rechazó permiso GPS en navegador
    - GPS deshabilitado en el dispositivo
    - Cobertura GPS deficiente
SOLUCIÓN:
    - Aceptar permiso de GPS
    - Habilitar GPS en dispositivo
    - Acercarse a ventana/exterior

PROBLEMA: "Fuera del rango permitido"
CAUSA: Usuario está lejos de la oficina
SOLUCIÓN:
    - Ir a la oficina, o
    - Ajustar radio_permitido_metros en ConfiguracionGPS

PROBLEMA: GPS no funciona en desarrollo (DEBUG=True, HTTP)
CAUSA: Navegador requiere HTTPS para Geolocation
SOLUCIÓN: 
    - Usar HTTPS en producción
    - En desarrollo: localhost funciona con HTTP
    - O configurar navegador para permitir HTTP en localhost
"""

# ============================================================================
# 9. LISTA DE VERIFICACIÓN (CHECKLIST)
# ============================================================================

"""
✅ COMPLETADO:
  [✓] Migraciones creadas y aplicadas
  [✓] Modelos actualizados con campos GPS
  [✓] Funciones de utilidad para Haversine
  [✓] Endpoint de validación /validar-gps/
  [✓] JavaScript mejorado en dashboard
  [✓] Integración con botones de marcación
  [✓] Comando CLI para configurar GPS
  [✓] Documentación completa
  [✓] Ejemplos de código
  [✓] Archivos de guía visual

📋 POR HACER (OPCIONAL):
  [ ] Hacer GPS obligatorio
  [ ] Dashboard admin con mapa
  [ ] Reportes con gráficos
  [ ] Alertas automáticas
  [ ] Notificaciones de marcación remota
  [ ] Auditoría de GPS
  [ ] Múltiples sedes/oficinas
  [ ] Geofencing avanzado
"""

# ============================================================================
# 10. CONTACTO Y AYUDA
# ============================================================================

"""
Para más información, consulta:
  - GPS_README.md - Guía rápida
  - GPS_VISUAL_GUIDE.md - Diagramas
  - asistencia/documentacion/gps-validacion.md - Documentación técnica
  - asistencia/ejemplos_gps.py - Ejemplos avanzados

¡El sistema está listo para usar! 🎉
"""

# ============================================================================
if __name__ == "__main__":
    print(__doc__)
