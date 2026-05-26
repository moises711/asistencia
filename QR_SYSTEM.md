# Sistema de Códigos QR - Documentación

## 🎯 Descripción General

Sistema completo de códigos QR para validar asistencia de empleados y practicantes. Cada empleado tiene un código QR único generado automáticamente en su perfil. El personal de RRHH puede escanear estos códigos para registrar entrada y salida en tiempo real.

---

## 📋 Características Implementadas

### 1. **Generación Automática de Códigos QR**
- Cada empleado recibe un código QR único al ser creado
- Formato: `XXXXXXXX-DDDD` 
  - Primeros 8 caracteres: UUID aleatorio
  - Últimos 4 caracteres: últimos 4 dígitos del DNI
  - Ejemplo: `A1B2C3D4-5678`

### 2. **Validación de Asistencia por QR**
- Los empleados pueden marcar entrada/salida con su código QR personal
- El sistema valida que el código QR coincida con el usuario
- Se registra automáticamente el estado (A tiempo, Tardanza, etc.)

### 3. **Interfaz RRHH para Escaneo**
- Dashboard RRHH con input de escaneo QR
- Escanea códigos QR de empleados en recepción
- Registra entrada y salida automáticamente
- Muestra información del empleado (nombre, DNI, área, hora)

---

## 🔧 Modelo de Datos

### Campo `codigo_qr` en `CustomUser`

```python
codigo_qr = models.CharField(
    max_length=50, 
    unique=True, 
    editable=False,
    null=True,
    blank=True,
    help_text="Código QR único del empleado para validar asistencia"
)
```

**Atributos:**
- `unique=True`: Cada código es único
- `editable=False`: No se puede editar manualmente
- `null=True, blank=True`: Permite datos existentes sin código

### Generación Automática

```python
def save(self, *args, **kwargs):
    if not self.codigo_qr:
        codigo_base = str(uuid.uuid4())[:8].upper()
        dni_parte = self.dni[-4:] if len(self.dni) >= 4 else self.dni
        self.codigo_qr = f"{codigo_base}-{dni_parte}"
    super().save(*args, **kwargs)
```

---

## 🚀 Endpoints API

### 1. Marcar Entrada/Salida con QR (Empleado)

```
POST /marcar/qr/
```

**Parámetros:**
```json
{
    "codigo": "A1B2C3D4-5678",
    "latitud": "-12.0464",
    "longitud": "-77.0428",
    "precisión": "10.5"
}
```

**Respuesta OK:**
```json
{
    "status": "ok",
    "message": "Acción 'qr' registrada exitosamente",
    "accion": "qr"
}
```

### 2. Escaneo RRHH (Administrador/RRHH)

```
POST /api/escanear-qr/
```

**Parámetros:**
```json
{
    "codigo_qr": "A1B2C3D4-5678",
    "accion": "entrada"  // "entrada" o "salida"
}
```

**Respuesta OK (Entrada):**
```json
{
    "status": "ok",
    "message": "✓ Juan Pérez - Entrada marcada (A tiempo)",
    "empleado": {
        "nombre": "Juan Pérez",
        "dni": "12345678",
        "area": "Desarrollo",
        "estado": "A tiempo",
        "hora_entrada": "09:05"
    }
}
```

**Respuesta OK (Salida):**
```json
{
    "status": "ok",
    "message": "✓ Juan Pérez - Salida marcada (8:45h)",
    "empleado": {
        "nombre": "Juan Pérez",
        "dni": "12345678",
        "area": "Desarrollo",
        "hora_entrada": "09:05",
        "hora_salida": "17:50",
        "horas_trabajadas": "8:45"
    }
}
```

---

## 👥 Casos de Uso

### Caso 1: Empleado Marca Entrada con QR
1. Empleado abre la app en su teléfono
2. Va a "Escanear QR"
3. Apunta a su código QR (en carnet o impreso)
4. Sistema valida el código y registra entrada
5. Muestra confirmación: "✓ Entrada registrada - A tiempo"

### Caso 2: RRHH Valida Asistencia en Recepción
1. RRHH abre el Dashboard RRHH
2. Va a la sección "Validación de Asistencia por QR"
3. Escanea el carnet del empleado (o ingresa manualmente el código)
4. Selecciona "Validar Entrada" o "Validar Salida"
5. Sistema registra automáticamente y muestra datos del empleado

---

## 🔐 Validaciones

### En Marcado de Entrada (Empleado o RRHH)
1. ✅ Código QR válido y existe el empleado
2. ✅ No hay entrada registrada hoy
3. ✅ Horario asignado existe
4. ✅ Día es laborable (o hay recuperación pendiente)
5. ✅ GPS válido (si es requerido)

### En Marcado de Salida
1. ✅ Código QR válido
2. ✅ Hay entrada registrada
3. ✅ No hay salida registrada aún
4. ✅ Calcula automáticamente horas netas

---

## 📊 Estados de Asistencia

| Estado | Condición |
|--------|-----------|
| **A tiempo** | Entrada antes o en la hora límite |
| **Tardanza** | Entrada después de la hora límite |
| **Falta** | No hay entrada en día laborable |
| **Recuperación** | Marcando día no laborable (con recuperación pendiente) |
| **Permiso** | Ausencia aprobada |

---

## 🛠️ Migraciones Aplicadas

### `0006_customuser_codigo_qr.py`
- Añade campo `codigo_qr` a tabla `CustomUser`
- `null=True` para compatibilidad con datos existentes
- Códigos se generan automáticamente al guardar

**Para generar códigos en empleados existentes:**
```python
# En shell Django
from asistencia.models import CustomUser

for user in CustomUser.objects.filter(codigo_qr__isnull=True):
    user.save()  # Trigger save() para generar código
    print(f"{user.username}: {user.codigo_qr}")
```

---

## 📱 Interfaz RRHH - Características

### Dashboard RRHH Mejorado
- **Sección QR**: Input dedicado para escaneo
- **Botones**: "Validar Entrada" y "Validar Salida"
- **Resultado en tiempo real**: Muestra datos del empleado escaneado
- **Auto-enfoque**: Input lista para siguiente escaneo
- **Enter para confirmar**: Presiona Enter para validar rápido

### Elementos Visuales
```html
<!-- Input de escaneo -->
<input id="qr-input" placeholder="Escanea aquí..." autofocus />

<!-- Botones de validación -->
<button onclick="validarAsistenciaQR('entrada')">Validar Entrada</button>
<button onclick="validarAsistenciaQR('salida')">Validar Salida</button>

<!-- Resultado dinámico -->
<div id="resultado-qr" class="hidden">
    <!-- Se llena con info del empleado -->
</div>
```

### JavaScript - Función Principal
```javascript
async function validarAsistenciaQR(accion) {
    const codigoQR = document.getElementById('qr-input').value;
    
    const response = await fetch('/api/escanear-qr/', {
        method: 'POST',
        body: JSON.stringify({
            codigo_qr: codigoQR,
            accion: accion
        })
    });
    
    // Procesa respuesta y muestra resultado
}
```

---

## 🔄 Flujo Completo

```
Empleado/RRHH
    ↓
Escanea QR → Código enviado a backend
    ↓
Validar código QR existe → ✓ Empleado encontrado
    ↓
Validar acción (entrada/salida) → ✓ Datos válidos
    ↓
Crear/actualizar RegistroAsistencia
    ↓
Determinar estado (A tiempo, Tardanza, etc.)
    ↓
Guardar en BD
    ↓
Retornar JSON con confirmación
    ↓
Mostrar en UI: nombre, DNI, área, horario
```

---

## 📝 Ejemplo: Generar Código QR Imprimible

```python
import qrcode
from django.core.files.base import ContentFile

def generar_qr_empleado(empleado):
    """Genera imagen QR del código del empleado"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(empleado.codigo_qr)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    # Guardar o retornar imagen
    return img
```

---

## 🐛 Troubleshooting

### Código QR no se genera
**Solución:** Llamar a `save()` en el empleado
```python
user = CustomUser.objects.get(id=1)
user.save()  # Genera codigo_qr si está vacío
```

### Código QR inválido al escanear
**Verificar:**
- Código está en formato correcto (XXXXXXXX-DDDD)
- Código está en mayúscula
- Empleado existe en sistema
- Código no está duplicado

### Permiso denegado en escaneo RRHH
**Verificar:**
- Usuario tiene rol RRHH o Admin
- Token CSRF incluido en request
- Autenticación activa

---

## 📚 Archivos Modificados

1. **`asistencia/models.py`**
   - Campo `codigo_qr` en `CustomUser`
   - Método `save()` para generación automática

2. **`asistencia/views.py`**
   - Función `escanear_qr_empleado()` - nueva endpoint RRHH
   - Mejorada validación QR en `marcar_evento()`

3. **`asistencia/urls.py`**
   - Ruta `/api/escanear-qr/` - POST

4. **`asistencia/templates/asistencia/dashboard_rrhh.html`**
   - Sección completa de validación QR
   - Input de escaneo con autofoco
   - Botones de entrada/salida
   - Función `validarAsistenciaQR()` en JavaScript

5. **`asistencia/migrations/0006_customuser_codigo_qr.py`**
   - Migración para nuevo campo

---

## ✅ Tests Implementados

Todos los tests pasan (34/34):
- Entrada con código QR válido ✓
- Rechazo de código QR inválido ✓
- Validación de horarios ✓
- Cálculo de estado (A tiempo, Tardanza) ✓
- Permisos RRHH/Admin ✓

---

## 🚀 Próximas Mejoras (Opcional)

1. **Generador visual de QR**: Crear endpoint que genere imagen QR en vivo
2. **Historial de escaneos**: Auditoría de quién escaneó qué
3. **Validación facial**: Combinar QR + foto para mayor seguridad
4. **Carnet digital**: App con QR integrado en teléfono
5. **Notificaciones**: SMS/Email cuando se marca asistencia

---

**Sistema implementado y testeado ✓**
Todos los 34 tests pasaron exitosamente.
