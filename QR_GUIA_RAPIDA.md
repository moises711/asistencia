# Guía Rápida: Sistema Optimizado de QR y GPS

## 🚀 Para Usar el Sistema

### RRHH: Escanear QR de Empleados
```
1. Ir a: http://192.168.1.54:8000/rrhh/
2. Hacer clic en el botón "ESCANEAR QR"
3. Permitir acceso a cámara cuando se solicite
4. Escanear el código QR del empleado/practicante
5. Entrada se marca INMEDIATAMENTE ✓
```

⏱️ **Tiempo**: Menos de 2 segundos (sin esperar GPS)

### Empleado: Marcar Entrada Manual (si no usa QR)
```
1. Ir a: http://192.168.1.54:8000/dashboard/
2. Permitir acceso a GPS cuando se solicite
3. Esperar validación de ubicación (debe estar en oficina)
4. Hacer clic en "ENTRADA"
5. Se registra entrada
```

⏱️ **Tiempo**: 3-5 segundos (incluye validación GPS)

### Empleado: Marcar Salida
```
1. En el dashboard, escribir actividades realizadas
2. Hacer clic en "SALIDA"
3. Se registra salida
```

⏱️ **Tiempo**: 1-2 segundos

## ✨ Cambios Principales

### ¿Qué pasó con la lentitud de GPS?
- **Antes**: Al escanear QR, se esperaba a que se validara GPS (lento)
- **Ahora**: Al escanear QR, se marca entrada INMEDIATAMENTE
- GPS se captura en background sin bloquear

### ¿Se puede marcar entrada sin estar en la oficina?
- **Si usa QR**: SÍ, el QR es la validación (se asume que es válido)
- **Si entra manual**: NO, requiere estar dentro del radio de GPS (500m aprox)

## 📱 Requisitos para Usar GPS

- Browser moderno (Chrome, Firefox, Safari, Edge)
- HTTPS o localhost (requerido para acceso a GPS)
- Permisos de ubicación habilitados

## 🔧 Configuración GPS (Admin)

Si necesitas cambiar la ubicación o radio de la oficina:
```
1. Ir a: http://192.168.1.54:8000/admin/
2. Buscar "Configuración GPS"
3. Editar coordenadas y radio permitido
```

## 📊 Datos Guardados

### Para Entrada por QR
- ✓ Hora de entrada
- ✓ Ubicación GPS (si está disponible)
- ✓ Precisión del GPS
- ✓ IP del dispositivo

### Para Salida
- ✓ Hora de salida
- ✓ Ubicación GPS (si está disponible)
- ✓ Actividades realizadas

## 🐛 Solución de Problemas

### "No me deja escanear QR"
→ Asegúrate de que la cámara está habilitada en el navegador

### "QR se escanea pero no marca entrada"
→ Verifica que el empleado existe en la base de datos con código QR asignado

### "Dice que estoy fuera de la oficina"
→ Pide acceso a GPS, puede que lo hayas rechazado

### "Es lento obtener GPS"
→ Esto es normal si usas entrada MANUAL. El QR es mucho más rápido.

## 📈 Rendimiento

| Operación | Tiempo | Validaciones |
|-----------|--------|---|
| Escaneo QR | <2s | Validar código QR + empleado |
| Entrada Manual | 3-5s | GPS + Horario + Validar |
| Salida | 1-2s | Actividades |

## 💡 Recomendación

**Usar siempre QR para entrada** → Es más rápido y confiable
- ✓ Instantáneo
- ✓ No requiere GPS
- ✓ Validación precisa
