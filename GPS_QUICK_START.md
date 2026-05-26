# 🎯 GUÍA PASO A PASO - Sistema GPS de Asistencia

## ✅ ESTADO: COMPLETADO

Todo el sistema está instalado, migraciones aplicadas y listo para usar.

---

## 📋 PASOS PARA EMPEZAR

### PASO 1: Configurar Ubicación de la Oficina
```bash
cd /home/sonjin/Empresa/proyect-python/control_asistencia
source env/bin/activate
python manage.py configurar_gps \
  --latitud 10.5123456 \
  --longitud -75.3456789 \
  --radio 20 \
  --nombre "Oficina Principal"
```

**Resultado esperado:**
```
✓ Configuración GPS creada/actualizada:
  - Nombre: Oficina Principal
  - Latitud: 10.5123456
  - Longitud: -75.3456789
  - Radio: 500m
```

### PASO 2: Iniciar Servidor Django
```bash
python manage.py runserver
```

**Resultado esperado:**
```
Starting development server at http://127.0.0.1:8000/
```

### PASO 3: Acceder al Dashboard
- Abre: http://localhost:8000/dashboard/
- Inicia sesión con un empleado

### PASO 4: Probar GPS
- Click en botón "📍 Ubicación GPS"
- Permite acceso a GPS cuando el navegador lo pida
- Espera a que muestre ubicación
- Verás: ✓ "En la oficina (XXXm)" o ✗ "Fuera de rango"

### PASO 5: Marcar Asistencia
- Click en "Marcar entrada"
- Se guardan coordenadas automáticamente
- ¡Listo!

---

## 🔍 VERIFICAR QUE TODO FUNCIONA

### En Django Shell:
```bash
python manage.py shell

# Ver configuración GPS
from asistencia.models import ConfiguracionGPS
config = ConfiguracionGPS.obtener_configuracion_activa()
print(f"Oficina: {config.nombre}")
print(f"Ubicación: ({config.latitud}, {config.longitud})")
print(f"Radio: {config.radio_permitido_metros}m")

# Ver registros con GPS
from asistencia.models import RegistroAsistencia
registros = RegistroAsistencia.objects.filter(
    latitud_entrada__isnull=False
)
print(f"Registros con GPS: {registros.count()}")

# Ver detalles de un registro
registro = registros.first()
if registro:
    print(f"Empleado: {registro.empleado}")
    print(f"Fecha: {registro.fecha}")
    print(f"Entrada: ({registro.latitud_entrada}, {registro.longitud_entrada})")
    print(f"Precisión: {registro.precisión_entrada}m")
```

### En la BD (SQL):
```sql
-- Ver configuración GPS
SELECT * FROM asistencia_configuraciongps WHERE activa = true;

-- Ver registros con GPS
SELECT empleado_id, fecha, latitud_entrada, longitud_entrada, 
       hora_entrada FROM asistencia_registroasistencia 
WHERE latitud_entrada IS NOT NULL LIMIT 10;

-- Contar registros por tipo
SELECT COUNT(*) as total,
       COUNT(CASE WHEN latitud_entrada IS NOT NULL THEN 1 END) as con_gps,
       COUNT(CASE WHEN latitud_entrada IS NULL THEN 1 END) as sin_gps
FROM asistencia_registroasistencia;
```

---

## 📂 ARCHIVOS PRINCIPALES

### Documentación
- `GPS_README.md` - Guía rápida
- `GPS_VISUAL_GUIDE.md` - Diagramas y flujos
- `GPS_IMPLEMENTATION_SUMMARY.txt` - Este resumen
- `asistencia/documentacion/gps-validacion.md` - Técnica completa

### Código
- `asistencia/models.py` - Modelos con GPS
- `asistencia/views.py` - Vistas y endpoint
- `asistencia/utils.py` - Funciones de GPS
- `asistencia/templates/asistencia/dashboard.html` - Frontend

### Utilidades
- `asistencia/management/commands/configurar_gps.py` - Comando
- `asistencia/ejemplos_gps.py` - Ejemplos de código
- `SETUP_GPS.py` - Setup documentation

---

## 🧪 PRUEBAS ÚTILES

### Test 1: Verificar Configuración
```python
from asistencia.models import ConfiguracionGPS
assert ConfiguracionGPS.obtener_configuracion_activa() is not None, \
    "ConfiguracionGPS no configurada"
print("✓ Configuración OK")
```

### Test 2: Probar Cálculo de Distancia
```python
from asistencia.utils import calcular_distancia_gps

# Misma ubicación = 0 metros
d = calcular_distancia_gps(10.5, -75.3, 10.5, -75.3)
assert d == 0, f"Distancia igual debería ser 0, got {d}"

# Ubicaciones diferentes
d = calcular_distancia_gps(10.5, -75.3, 10.6, -75.2)
assert d > 0, "Distancia debería ser mayor a 0"
print(f"✓ Distancia calculada: {d:.2f}m")
```

### Test 3: Probar Validación
```python
from asistencia.utils import validar_ubicacion_gps
from asistencia.models import ConfiguracionGPS

config = ConfiguracionGPS.obtener_configuracion_activa()

# Dentro del rango
resultado = validar_ubicacion_gps(
    config.latitud, config.longitud,  # Misma ubicación
    config.latitud, config.longitud,
    500
)
assert resultado['valido'] == True, "Misma ubicación debería ser válida"
print("✓ Validación OK")
```

---

## ⚙️ CAMBIOS EN CONFIGURACIÓN

### Cambiar Radio Permitido
```python
config = ConfiguracionGPS.objects.first()
config.radio_permitido_metros = 300  # Más restrictivo
config.save()
```

### Cambiar Ubicación de Oficina
```python
config = ConfiguracionGPS.objects.first()
config.latitud = 10.6123456
config.longitud = -75.4456789
config.save()
```

### Desactivar GPS Temporalmente
```python
ConfiguracionGPS.objects.filter(activa=True).update(activa=False)
# O
config = ConfiguracionGPS.objects.first()
config.activa = False
config.save()
```

---

## 🚨 TROUBLESHOOTING

### Error: "Configuración GPS no disponible"
```bash
# Verificar si existe configuración
python manage.py shell
>>> from asistencia.models import ConfiguracionGPS
>>> ConfiguracionGPS.objects.count()
0  # Si retorna 0, crear configuración

# Crear configuración
>>> ConfiguracionGPS.objects.create(
...     nombre="Oficina Principal",
...     latitud=10.5,
...     longitud=-75.3,
...     radio_permitido_metros=500,
...     activa=True
... )
```

### Error: "GPS no funciona en dashboard"
1. Verificar que HTTPS esté en producción
2. En desarrollo, localhost HTTP funciona
3. Permitir GPS en navegador (Chrome: ⚙️ → Privacidad)
4. Verificar que dispositivo tenga GPS habilitado

### Error: "Coordenadas no se guardan"
1. Verificar que migración se aplicó: `python manage.py migrate`
2. Verificar que JSON se envía correctamente
3. Revisar logs de Django para errores

---

## 📊 REPORTES

### Ver registros con GPS por empleado
```python
from asistencia.ejemplos_gps import generar_reporte_gps_por_empleado
from asistencia.models import CustomUser

empleado = CustomUser.objects.first()
reporte = generar_reporte_gps_por_empleado(empleado)
print(reporte)
```

### Ver empleados que marcaron fuera de rango
```python
from asistencia.ejemplos_gps import obtener_asistencias_remotas
from django.utils import timezone

remotas = obtener_asistencias_remotas(timezone.localdate())
for item in remotas:
    print(f"{item['registro'].empleado}: {item['distancia']}m")
```

### Generar reporte de cumplimiento diario
```python
from asistencia.ejemplos_gps import generar_reporte_cumplimiento_gps
from django.utils import timezone

reporte = generar_reporte_cumplimiento_gps(timezone.localdate())
print(f"Total: {reporte['total_registros']}")
print(f"Con GPS: {reporte['con_gps']}")
print(f"Sin GPS: {reporte['sin_gps']}")
print(f"En rango: {reporte['dentro_rango']}")
print(f"Fuera de rango: {reporte['fuera_rango']}")
```

---

## 🔄 CICLO DE USO TÍPICO

1. **Admin configura oficina**
   ```bash
   python manage.py configurar_gps --latitud X --longitud Y
   ```

2. **Usuario abre dashboard**
   - Accede a http://localhost:8000/dashboard/

3. **Usuario solicita GPS**
   - Click en "Ubicación GPS"
   - Permite acceso

4. **Sistema valida**
   - POST /validar-gps/ con coordenadas
   - Calcula distancia
   - Muestra resultado

5. **Usuario marca entrada**
   - Click "Marcar entrada"
   - Se envían coordenadas
   - Se guardan en BD

6. **Admin revisa reportes**
   - Ver registros con GPS
   - Generar reportes
   - Identificar empleados remotos

---

## ✨ ¡LISTO!

El sistema está completamente implementado y funcionando.

**Para empezar ahora:**
```bash
cd /home/sonjin/Empresa/proyect-python/control_asistencia
source env/bin/activate
python manage.py configurar_gps --latitud 10.5 --longitud -75.3 --radio 500
python manage.py runserver
# Abre http://localhost:8000/dashboard/
```

¡Disfruta del sistema de GPS! 🎉
