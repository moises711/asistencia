# Flujos de Validación de Asistencia - Configuración Final

## 📋 Resumen de los Casos de Uso

### Caso 1: Empleado marca entrada desde su dashboard (REQUIERE GPS OBLIGATORIO)
**Ubicación**: `http://192.168.1.54:8000/dashboard/`

```
1. Empleado accede a su dashboard
2. Hace clic en "Marcar entrada"
   ├─ Si requiere GPS (no tiene permiso remoto):
   │  └─> Se abre automáticamente el diálogo de GPS
   │     └─> DEBE compartir ubicación (OBLIGATORIO)
   │        └─> Si está en oficina: Se marca entrada ✓
   │        └─> Si está fuera: Muestra error de ubicación ✗
   │
   └─ Si NO requiere GPS:
      └─> Marca entrada inmediatamente ✓
```

**Configuración**: El atributo `permite_remoto` en CustomUser determina esto
- `permite_remoto = True` → No requiere GPS
- `permite_remoto = False` → Requiere GPS (es la mayoría de empleados)

**Código JavaScript** (dashboard.html línea ~214):
```javascript
if ((accion === 'entrada') && REQUIERE_GPS && !gpsValido) {
    window.showToast('Primero comparte tu ubicación GPS', 'error');
    solicitarGPS();
    return;
}
```

---

### Caso 2: RRHH escanea código QR del empleado (SIN VALIDACIÓN GPS REQUERIDA)
**Ubicación**: `http://192.168.1.54:8000/rrhh/`

```
1. RRHH accede al panel de validación por QR
2. Abre la cámara (o ingresa código manualmente)
3. Escanea código QR del empleado
   ├─> Se envía inmediatamente a /api/escanear-qr/
   │   └─> Backend registra entrada del empleado
   │   └─> SIN validar GPS (el QR es la validación)
   │
4. Entrada se marca en <2 segundos ✓
5. Se muestra opción VOLUNTARIA: "¿Validar ubicación?"
   └─> RRHH puede hacer clic si quiere verificar
       └─> Se captura GPS del empleado
       └─> Se valida si está en oficina (informativo)
```

**Configuración**: El endpoint `/api/escanear-qr/` nunca valida GPS
- Solo verifica: código QR válido, empleado existe, horario
- **No requiere** ubicación GPS

**Código JavaScript** (dashboard_rrhh.html línea ~230):
```javascript
// Entrada por QR NO requiere GPS (se captura en background sin bloquear)
if (accion === 'qr' && REQUIERE_GPS && !gpsValido) {
    solicitarGPS(false); // Captura en BACKGROUND sin bloquear
}
```

---

## 📊 Matriz de Comportamiento

| Acción | Ubicación | GPS Requerido | Bloqueante | Resultado |
|--------|-----------|---|---|---|
| Entrada Manual | Dashboard Empleado | Sí (si no permite_remoto) | SÍ | Marca si está en oficina |
| Entrada por QR | Dashboard RRHH | NO | No | Marca inmediatamente |
| Validación GPS (Post-QR) | Dashboard RRHH | NO (Opcional) | No | Informativo: si está en oficina |
| Salida | Dashboard Empleado | NO | No | Registra actividades |

---

## 🔐 Flujos Detallados

### FLUJO A: Empleado Temprano sin RRHH (Dashboard)
**Caso**: "A veces llego temprano y no hay RRHH, me valido yo mismo"

```
1. Empleado ingresa a http://192.168.1.54:8000/dashboard/
2. Hace clic en "Marcar entrada"
3. Sistema requiere GPS
   └─> Pop-up: "Calculo de ubicación..."
   └─> Solicita permisos de geolocalización
4. Empleado comparte ubicación
   └─> Sistema valida: ¿está en oficina?
   └─> RRHH requiere estar dentro de 500m de oficina
5. ✓ Entrada registrada (si cumple)
   ✗ Error de ubicación (si está fuera)
```

**Tiempo**: 3-5 segundos (incluye validación GPS)  
**Requisito**: GPS obligatorio

---

### FLUJO B: Entrada por QR en Recepción (RRHH)
**Caso**: "RRHH escanea QR de empleado al llegar"

```
1. RRHH abre http://192.168.1.54:8000/rrhh/
2. Hace clic en "ESCANEAR QR"
   └─> Abre cámara
3. Escanea el código QR del empleado
   └─> Se envía código al servidor
   └─> Backend registra entrada inmediatamente
4. ✓ Entrada marcada (instantáneo)
5. Se muestra: "¿Validar ubicación?"
   └─> RRHH puede hacer clic SI QUIERE
   └─> Si hace clic: Se captura GPS del empleado
       └─> Muestra: "Está en oficina" o "Fuera de oficina"
       └─> Es solo informativo
```

**Tiempo**: <2 segundos (sin esperar GPS)  
**Requisito**: GPS opcional

---

### FLUJO C: Empleado sin Restricción de Ubicación (Remoto)
**Caso**: Empleado con `permite_remoto = True`

```
1. Accede a su dashboard
2. Hace clic en "Marcar entrada"
3. ✓ Entrada registrada inmediatamente (sin GPS)
4. Hace clic en "Marcar salida"
5. ✓ Salida registrada con descripción de actividades
```

**Tiempo**: <1 segundo  
**Requisito**: Sin GPS

---

## 🎯 Puntos Clave de Implementación

### 1. Validación GPS en Backend (`views.py`)
```python
def requiere_validacion_gps(usuario: CustomUser) -> bool:
    return not usuario.permite_remoto  # True = requiere GPS

def validar_gps_para_marcacion(usuario, latitud, longitud):
    if not requiere_validacion_gps(usuario):
        return None  # No valida GPS
    
    # ... valida ubicación contra oficina
```

### 2. Endpoint `/api/escanear-qr/` (views.py línea ~825)
- **NO valida GPS** antes de registrar
- Solo verifica código QR + empleado
- GPS es completamente opcional

### 3. Función `solicitarGPS()` con Parámetro (dashboard_rrhh.html)
```javascript
function solicitarGPS(mostrarStatus = true) {
    // Si mostrarStatus = false: captura en background
    // Si mostrarStatus = true: bloquea y valida con servidor
}
```

---

## 🧪 Guía de Prueba

### Prueba 1: Entrada Manual desde Dashboard (Requiere GPS)
```bash
1. Login como empleado (no remoto)
2. Ir a http://192.168.1.54:8000/dashboard/
3. Hacer clic en "Marcar entrada"
   Esperado: Se abre automáticamente diálogo de GPS
   ✓ DEBE pedirse ubicación obligatoriamente
4. Compartir ubicación
5. ✓ Si está en oficina: Se marca entrada
   ✗ Si está fuera: Error de ubicación
```

### Prueba 2: Escaneo QR (NO requiere GPS)
```bash
1. Ir a http://192.168.1.54:8000/rrhh/
2. Hacer clic en "ESCANEAR QR"
3. Escanear código QR
   Esperado: Entrada marcada en <2 segundos
   ✓ NO debe pedir GPS obligatoriamente
4. Se muestra opción: "¿Validar ubicación?"
5. Hacer clic en "Validar GPS" (opcional)
   Esperado: Muestra si está en oficina
```

### Prueba 3: Empleado Remoto
```bash
1. Login como empleado con permite_remoto=True
2. Ir a dashboard
3. Hacer clic en "Marcar entrada"
   Esperado: Marca inmediatamente
   ✓ NO pide GPS
```

---

## 📝 Notas Importantes

1. **`permite_remoto` es la clave**: Determina si se requiere GPS
2. **QR es lo más rápido**: Use QR cuando sea posible (entrada por RRHH)
3. **GPS es seguro**: Solo valida cuando es necesario (entrada manual)
4. **Validación post-QR es informativa**: Para que RRHH verifique ubicación si lo desea

---

## 🔗 Endpoints Clave

| Endpoint | Método | GPS Requerido | Descripción |
|----------|--------|---|---|
| `/marcar/entrada/` | POST | Sí (si aplica) | Empleado marca entrada |
| `/marcar/salida/` | POST | No | Empleado marca salida |
| `/api/escanear-qr/` | POST | NO | RRHH escanea código QR |
| `/validar-gps/` | POST | N/A | Validar ubicación (voluntario) |

---

## ✅ Resumen Final

✓ **Entrada Manual (Dashboard)**: GPS OBLIGATORIO (si corresponde)  
✓ **Entrada por QR (RRHH)**: GPS NO REQUERIDO (opcional validar después)  
✓ **Salida**: Sin validación GPS  
✓ **Rendimiento**: QR <2s, entrada manual 3-5s, salida 1-2s
