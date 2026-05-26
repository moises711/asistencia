# Validación de Coordenadas GPS para Control de Asistencia

## Descripción General

Se ha implementado un sistema completo para capturar y validar las coordenadas GPS del usuario al marcar asistencia. Esto permite verificar que el empleado esté dentro del radio permitido de la oficina.

## Componentes Implementados

### 1. **Modelo: ConfiguracionGPS**
Almacena la configuración de ubicación de la oficina:
- `nombre`: Nombre de la oficina
- `latitud`: Coordenada de latitud de la oficina
- `longitud`: Coordenada de longitud de la oficina
- `radio_permitido_metros`: Radio en metros (default: 500m)
- `activa`: Si la configuración está activa

```python
# Uso en código
config = ConfiguracionGPS.obtener_configuracion_activa()
```

### 2. **Campos en RegistroAsistencia**
Se agregaron campos para guardar las coordenadas GPS:
- `latitud_entrada`: Latitud al marcar entrada
- `longitud_entrada`: Longitud al marcar entrada
- `latitud_salida`: Latitud al marcar salida
- `longitud_salida`: Longitud al marcar salida
- `precisión_entrada`: Precisión GPS en metros (entrada)
- `precisión_salida`: Precisión GPS en metros (salida)

### 3. **Funciones de Utilidad (utils.py)**

#### `calcular_distancia_gps(lat1, lon1, lat2, lon2)`
Calcula la distancia entre dos coordenadas usando la fórmula de Haversine.
```python
distancia = calcular_distancia_gps(10.5, -75.3, 10.6, -75.2)
# Retorna: distancia en metros
```

#### `validar_ubicacion_gps(latitud_usuario, longitud_usuario, latitud_oficina, longitud_oficina, radio_permitido_metros=500)`
Valida si el usuario está dentro del radio permitido.
```python
resultado = validar_ubicacion_gps(10.5, -75.3, 10.6, -75.2, 500)
# Retorna: {
#   'valido': bool,
#   'distancia': float,
#   'mensaje': str
# }
```

### 4. **Vista: validar_gps**
Endpoint para validar las coordenadas GPS del usuario.

**URL:** `POST /validar-gps/`

**Body (JSON):**
```json
{
  "latitud": 10.5123456,
  "longitud": -75.3456789,
  "precisión": 5.5
}
```

**Response (JSON):**
```json
{
  "valido": true,
  "distancia": 145.32,
  "mensaje": "Distancia: 145.32m - Ubicación válida",
  "precision": 5.5,
  "radio_permitido": 500
}
```

### 5. **JavaScript Frontend (dashboard.html)**

#### Variable Global: `coordenadasGPS`
Almacena las coordenadas del usuario después de validarlas.
```javascript
coordenadasGPS = {
  latitud: null,
  longitud: null,
  precisión: null
}
```

#### Función: `solicitarGPS()`
Captura las coordenadas del dispositivo y las valida con el servidor.
- Muestra el estado en tiempo real
- Valida que esté dentro del radio permitido
- Almacena las coordenadas si son válidas

#### Integración con Marcación
Al marcar entrada o salida, si las coordenadas están disponibles, se envían al servidor:
```javascript
// Las coordenadas se envían en FormData
formData.append('latitud', coordenadasGPS.latitud);
formData.append('longitud', coordenadasGPS.longitud);
formData.append('precisión', coordenadasGPS.precisión);
```

## Configuración

### 1. Configurar Coordenadas de la Oficina

**Opción A: Usar el comando Django**
```bash
python manage.py configurar_gps \
  --latitud 10.5123456 \
  --longitud -75.3456789 \
  --radio 20 \
  --nombre "Oficina Principal"
```

**Opción B: Desde el shell de Django**
```python
from asistencia.models import ConfiguracionGPS

ConfiguracionGPS.objects.filter(activa=True).update(activa=False)
ConfiguracionGPS.objects.create(
    nombre="Oficina Principal",
    latitud=10.5123456,
    longitud=-75.3456789,
    radio_permitido_metros=500,
    activa=True
)
```

**Opción C: Desde el admin**
Acceder a `http://localhost:8000/admin/asistencia/configuraciongps/`

### 2. Radio Permitido
El radio permitido (default: 500m) se puede ajustar según necesidades:
- 100m: Muy restrictivo, solo dentro del edificio
- 300m: Restrictivo, área inmediata
- 500m: Moderado (default)
- 1000m: Permisivo, manzana completa

## Flujo de Uso

1. **Usuario abre el dashboard**
   - Haz clic en "Ubicación GPS"

2. **Sistema solicita permisos**
   - Navegador pide permiso para acceder a GPS
   - Usuario acepta

3. **Sistema captura coordenadas**
   - Se obtienen lat, lon y precisión
   - Se valida contra la ubicación de la oficina

4. **Mostrar resultado**
   - ✓ Verde: "En la oficina (145m)" - Ubicación válida
   - ✗ Rojo: "Fuera de rango (2500m)" - No válida

5. **Marcar asistencia**
   - Si GPS es válido: Se envían coordenadas al servidor
   - Se guardan en RegistroAsistencia
   - Si GPS no es válido: Se puede marcar igual (sin validación GPS)

## Casos de Uso

### 1. Validación Requerida
Si deseas hacer GPS obligatorio:
```python
# En views.py, función marcar_evento
if accion == "entrada":
    config_gps = ConfiguracionGPS.obtener_configuracion_activa()
    if not coordenadas_gps_validas:
        return JsonResponse({
            'status': 'error',
            'message': 'Debes estar en la oficina para marcar entrada'
        }, status=403)
```

### 2. Registro de Auditoría
Ver dónde estaba el usuario cuando marcó:
```python
# En reportes
registro = RegistroAsistencia.objects.first()
print(f"Entrada: {registro.latitud_entrada}, {registro.longitud_entrada}")
print(f"Precisión: {registro.precisión_entrada}m")
```

### 3. Reportes de Cumplimiento
```python
# Empleados que marcaron desde la oficina
desde_oficina = RegistroAsistencia.objects.filter(
    latitud_entrada__isnull=False,
    longitud_entrada__isnull=False
)

# Empleados con marcaciones remotas
remotas = RegistroAsistencia.objects.filter(
    latitud_entrada__isnull=True
)
```

## Errores Comunes

### "No se pudo obtener la ubicación"
- **Causa:** Navegador sin permiso, GPS deshabilitado, mala cobertura
- **Solución:** 
  - Permitir GPS en la configuración del navegador
  - Habilitar GPS en el dispositivo
  - Acercarse a ventana/exterior para mejor señal

### "Fuera del rango permitido"
- **Causa:** Usuario está alejado de la oficina
- **Solución:** Ir a la oficina o ajustar radio permitido

### "Precisión GPS desconocida"
- **Causa:** GPS no tiene señal clara
- **Solución:** Esperar o moverse a un lugar con mejor cobertura

## Seguridad

- Las coordenadas se validan en el servidor
- La precisión GPS se registra para auditoría
- Los datos se guardan encriptados (en base de datos)
- El radio permitido es configurable y auditable

## Notas Técnicas

- **Fórmula de Haversine**: Calcula distancia entre dos puntos en una esfera
- **Precisión GPS**: Típicamente 5-10m en ciudad
- **Tolerancia**: Se recomienda usar un radio de al menos 200m
- **Compatibilidad**: Funciona en navegadores modernos (Chrome, Firefox, Safari, Edge)
- **HTTPS**: Recomendado para producción (algunos navegadores requieren HTTPS para GPS)
