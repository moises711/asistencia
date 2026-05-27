# Guia de Uso de Horarios, Permisos y Feriados

## Proposito
Este documento explica como configurar y usar los horarios de trabajo, los permisos programados y los dias feriados en el sistema de control de asistencia.

## Quien puede gestionar esto
- Admin
- RRHH

## Flujo Basico de Uso

### 1. Entrar al modulo de horarios
1. Inicia sesion con un usuario Admin o RRHH.
2. Abre la ruta `/horarios/`.
3. Revisa la lista de horarios, feriados, ausencias y recuperaciones pendientes.

### 2. Crear un horario
1. En la seccion de horarios, completa el nombre del turno.
2. Define la hora de entrada y la hora de salida.
3. Configura la tolerancia en minutos.
4. Marca los dias laborables del turno.
5. Guarda el registro.

### 3. Asignar un horario a un empleado
1. Abre la vista de empleados.
2. Busca al colaborador.
3. Asigna el horario creado.
4. Guarda los cambios.

### 4. Registrar un feriado
1. Dentro de `/horarios/`, ve al bloque de feriados.
2. Agrega la fecha y la descripcion del feriado.
3. Guarda el feriado.
4. El sistema bloquea marcaciones en esa fecha.

### 5. Crear un permiso o ausencia programada
1. En `/horarios/`, ubica la seccion de ausencias o permisos.
2. Selecciona el empleado.
3. Indica la fecha de inicio y fin.
4. Agrega el motivo si corresponde.
5. Guarda y luego aprueba o rechaza el permiso.

### 6. Revisar recuperaciones pendientes
1. Verifica si existen recuperaciones generadas por faltas sin permiso.
2. Revisa el estado de cada recuperacion.
3. Si el empleado recupera horas, el sistema actualiza el estado.

## Como afecta el uso diario
- La entrada manual valida horario y, si aplica, GPS.
- La entrada por QR valida al empleado sin bloquear por GPS.
- La salida no debe pedir GPS.
- Los dias feriados y permisos aprobados bloquean o ajustan la marcacion segun la regla definida.

## Reglas practicas
- Si un empleado no tiene horario, no debe marcar entrada normal.
- Si un dia no es laborable, el sistema debe rechazar la marcacion salvo recuperacion pendiente.
- Si existe un feriado o un permiso aprobado, la asistencia se trata segun la regla del sistema.
- Si el usuario tiene permiso remoto, no se exige GPS.

## Verificacion rapida
- `/horarios/` muestra horarios activos.
- `/empleados/` permite asignar horarios.
- `/dashboard/` refleja el horario del usuario.
- `/marcar/entrada/` y `/marcar/salida/` usan la configuracion aplicada.

## Buenas practicas de uso
- Mantener un solo horario claro por empleado cuando sea posible.
- Revisar feriados antes de cerrar el mes.
- Aprobar permisos antes de la fecha para evitar bloqueos.
- Revisar recuperaciones despues de faltas justificadas.