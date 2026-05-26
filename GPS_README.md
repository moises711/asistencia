# 📍 Sistema de Validación GPS para Control de Asistencia

## Resumen de Implementación

Se ha creado un **sistema completo de validación de coordenadas GPS** para validar que los empleados marquen su asistencia desde la ubicación correcta (la oficina).

## ✨ Características Principales

✅ **Captura de coordenadas en tiempo real** - Obtiene GPS del dispositivo del usuario  
✅ **Validación de distancia** - Usa fórmula de Haversine para calcular distancia  
✅ **Radio configurableble** - Puedes ajustar el radio permitido (default: 20m)  
✅ **Almacenamiento de datos** - Guarda coordenadas y precisión GPS  
✅ **Endpoint de validación** - API para validar GPS antes de marcar  
✅ **Integración con dashboard** - Botón "Ubicación GPS" con validación en vivo  

## 📁 Archivos Modificados/Creados

### Modelos
- **[asistencia/models.py](asistencia/models.py)** ✏️
  - ✅ Nuevo: `ConfiguracionGPS` - Configura ubicación de oficina
  - ✅ Actualizado: `RegistroAsistencia` - Agregó 6 campos GPS

### Utilidades
- **[asistencia/utils.py](asistencia/utils.py)** ✏️
  - ✅ `calcular_distancia_gps()` - Fórmula de Haversine
  - ✅ `validar_ubicacion_gps()` - Valida si está en rango

### Vistas
- **[asistencia/views.py](asistencia/views.py)** ✏️
  - ✅ Nuevo: `validar_gps()` - Endpoint POST /validar-gps/
  - ✅ Mejorado: `marcar_evento()` - Ahora guarda GPS

### Frontend
- **[asistencia/templates/asistencia/dashboard.html](asistencia/templates/asistencia/dashboard.html)** ✏️
  - ✅ Nuevo: `coordenadasGPS` - Variable global
  - ✅ Mejorado: `solicitarGPS()` - Captura y valida
  - ✅ Mejorado: Botones de marcación - Envían GPS

### URLs
- **[asistencia/urls.py](asistencia/urls.py)** ✏️
  - ✅ Nueva ruta: `/validar-gps/`

### Migraciones
- **[asistencia/migrations/0003_...py](asistencia/migrations/)** ✅ Creada y aplicada

### Comandos
- **[asistencia/management/commands/configurar_gps.py](asistencia/management/commands/configurar_gps.py)** ✨ Nuevo
  - Comando: `python manage.py configurar_gps --latitud X --longitud Y --radio Z`

### Documentación
- **[asistencia/documentacion/gps-validacion.md](asistencia/documentacion/gps-validacion.md)** 📚 Nuevo
- **[asistencia/ejemplos_gps.py](asistencia/ejemplos_gps.py)** 📚 Nuevo

## 🚀 Inicio Rápido

### 1️⃣ Configurar ubicación de la oficina
```bash
python manage.py configurar_gps \
  --latitud 10.5123456 \
  --longitud -75.3456789 \
  --radio 20 \
  --nombre "Oficina Principal"
```

### 2️⃣ Usuario abre dashboard
El empleado ve el dashboard con botón "Ubicación GPS"

### 3️⃣ Validar GPS
- Click en "Ubicación GPS"
- Se capturan coordenadas
- Se validan contra la oficina configurada
- Status cambia a ✓ "En la oficina (145m)" o ✗ "Fuera de rango"

### 4️⃣ Marcar asistencia
- Click en "Marcar entrada" o "Marcar salida"
- Se envían coordenadas GPS al servidor
- Se guardan en la BD automáticamente

## 📊 Datos Guardados

Para cada entrada/salida se guardan:
- **Coordenadas**: Latitud y Longitud exactas
- **Precisión**: Margen de error en metros (GPS accuracy)
- **Distancia**: Calculada desde la oficina

## 🔧 Configuración Avanzada

### Ajustar radio permitido
```python
# En admin o shell
config = ConfiguracionGPS.objects.first()
config.radio_permitido_metros = 300  # Más restrictivo
config.save()
```

### Hacer GPS obligatorio (opcional)
```python
# En views.py, modificar marcar_evento()
if accion == 'entrada':
    if not coordenadas_gps_validas:
        return JsonResponse({
            'status': 'error',
            'message': 'GPS es requerido para marcar'
        }, status=403)
```

## 📋 API Endpoints

### POST /validar-gps/
Valida coordenadas GPS

**Request:**
```json
{
  "latitud": 10.5123456,
  "longitud": -75.3456789,
  "precisión": 5.5
}
```

**Response:**
```json
{
  "valido": true,
  "distancia": 145.32,
  "mensaje": "Distancia: 145.32m - Ubicación válida",
  "precision": 5.5,
  "radio_permitido": 500
}
```

### POST /marcar/entrada/
Marca entrada (ahora con GPS opcional)

**Request (FormData):**
```
latitud: 10.5123456
longitud: -75.3456789
precisión: 5.5
```

## 🗂️ Estructura de Base de Datos

### ConfiguracionGPS
```sql
- id (PK)
- nombre (CharField)
- latitud (DecimalField)
- longitud (DecimalField)
- radio_permitido_metros (IntegerField)
- activa (BooleanField)
- creada_en (DateTimeField)
- actualizada_en (DateTimeField)
```

### RegistroAsistencia (campos nuevos)
```sql
- latitud_entrada (DecimalField)
- longitud_entrada (DecimalField)
- latitud_salida (DecimalField)
- longitud_salida (DecimalField)
- precisión_entrada (FloatField)
- precisión_salida (FloatField)
```

## 🔍 Consultas Útiles

### Ver registros con GPS
```python
RegistroAsistencia.objects.filter(
    latitud_entrada__isnull=False
)
```

### Ver registros sin GPS
```python
RegistroAsistencia.objects.filter(
    latitud_entrada__isnull=True
)
```

### Generar reporte
```python
from asistencia.ejemplos_gps import generar_reporte_gps_por_empleado
reporte = generar_reporte_gps_por_empleado(empleado)
```

## ⚠️ Consideraciones Importantes

1. **HTTPS en Producción**: Algunos navegadores requieren HTTPS para GPS
2. **Permisos del Navegador**: El usuario debe permitir acceso a GPS
3. **Precisión GPS**: Varía 5-20m dependiendo de cobertura
4. **Offline**: GPS requiere conexión a internet (excepto GPS nativo)
5. **Privacidad**: Los datos de ubicación son sensibles, guardarlos con cuidado

## 📚 Documentación Adicional

Consulta los siguientes archivos para más información:
- [gps-validacion.md](asistencia/documentacion/gps-validacion.md) - Documentación completa
- [ejemplos_gps.py](asistencia/ejemplos_gps.py) - Ejemplos de código avanzado
- [models.py](asistencia/models.py) - Definición de modelos
- [utils.py](asistencia/utils.py) - Funciones de utilidad

---

✨ **¡Sistema listo para usar!** ✨
