📋 Documento de Especificación: Sistema de Control de Asistencia (Django)

Actúa como un Desarrollador Senior de Python/Django. Tu tarea es construir un sistema de control de asistencia basado en las siguientes especificaciones. Usa las mejores prácticas: vistas basadas en clases (CBVs), formularios limpios, Tailwind CSS para el diseño (vía CDN) y una arquitectura modular.
1. Requerimientos del Sistema (PRD)
Requerimientos Funcionales

    RF1: Autenticación y Roles: Tres tipos de usuarios: Administrador (RRHH), Supervisor y Empleado.

    RF2: Registro de Entrada/Salida: Los empleados deben poder marcar "Entrada" y "Salida" con un solo clic. El sistema debe capturar la hora exacta del servidor y la dirección IP (opcional: geolocalización).

    RF3: Gestión de Empleados: El Administrador puede crear, editar y dar de baja usuarios, además de asignarles un horario y un supervisor.

    RF4: Panel de Reportería: El Administrador y Supervisores pueden ver y exportar (PDF/Excel) las asistencias por rango de fecha, empleado o departamento.

    RF5: Justificaciones: El empleado puede solicitar la justificación de una falta o tardanza, adjuntando un motivo. El supervisor aprueba o rechaza.

Requerimientos No Funcionales

    RNF1: Base de datos: PostgreSQL (producción) / SQLite (desarrollo).

    RNF2: Seguridad: Middleware para restringir vistas según el rol del usuario.

    RNF3: Interfaz responsiva (Mobile-first para el marcado de asistencia).

2. Arquitectura de Base de Datos (Modelos)

Diseña los siguientes modelos en una app llamada asistencia:

[Usuario/Empleado] 1 ------- * [RegistroAsistencia]
       1                             1
       |                             |
       ----------------------- * [Justificacion]

    CustomUser (Hereda de AbstractUser):

        rol (Choices: 'admin', 'supervisor', 'empleado')

        dni (CharField, único)

        supervisor (ForeignKey a sí mismo, null=True)

    RegistroAsistencia:

        empleado (ForeignKey a CustomUser)

        fecha (DateField, auto_now_add=True)

        hora_entrada (DateTimeField, null=True)

        hora_salida (DateTimeField, null=True)

        estado (Choices: 'a_tiempo', 'tardanza', 'falta')

        ip_registro (GenericIPAddressField)

    Justificacion:

        asistencia (ForeignKey a RegistroAsistencia)

        motivo (TextField)

        estado (Choices: 'pendiente', 'aprobado', 'rechazado')

        revisado_por (ForeignKey a CustomUser, supervisor)

3. Procesos y Flujos de Trabajo (Workflows)

La IA debe programar la lógica de negocio respetando estos tres flujos principales:
Flujo A: Marcado de Asistencia (Lógica del Backend)

    El empleado entra a su panel y da clic en "Registrar Entrada".

    Validación: El sistema verifica si ya existe un registro para el día de hoy. Si no existe, crea el RegistroAsistencia y guarda la hora_entrada.

    Si la hora actual supera la hora de entrada oficial (ej. 09:00 AM), el estado cambia automáticamente a 'tardanza'.

    Por la tarde, el empleado da clic en "Registrar Salida". El sistema busca el registro de hoy y actualiza hora_salida.

Flujo B: Procesamiento Automático de Faltas (Celery o Comando Cron)

    Un comando personalizado de Django (python manage.py verificar_faltas) se ejecuta de lunes a viernes a las 11:00 AM.

    Busca todos los empleados activos que no tengan un registro de asistencia para el día en curso y les crea automáticamente un registro con el estado 'falta'.

4. Mapa de Vistas y URLs (Frontend/Backend)

Estructura el sistema con las siguientes URLs y utiliza plantillas HTML limpias con componentes de Tailwind CSS.
🔐 Autenticación

    /login/ -> Vista de inicio de sesión estándar de Django.

    /logout/ -> Cierre de sesión y redirección.

👤 Módulo de Empleado

    /dashboard/ -> Panel principal. Muestra la hora actual (reloj en tiempo real) y dos botones dinámicos: "Marcar Entrada" (activo si no ha marcado) y "Marcar Salida" (activo si ya marcó entrada pero no salida). Muestra también el historial de sus últimos 5 marcados.

    /justificaciones/nueva/<int:asistencia_id>/ -> Formulario para justificar una tardanza o falta.

📊 Módulo de Supervisor y Admin

    /panel-control/ -> Vista general. Gráficos rápidos (asistencias de hoy, tardanzas, faltas).

    /asistencias/reporte/ -> Tabla con filtros por fecha, empleado y estado. Botón para descargar reporte.

    /justificaciones/pendientes/ -> Lista de solicitudes. Botones de acción rápida: Aprobar / Rechazar vía AJAX/POST.

    /empleados/ -> CRUD completo para gestionar los usuarios del sistema.

5. Instrucciones de Entrega del Código

Para empezar a desarrollar el sistema, por favor genera los archivos en el siguiente orden, asegurándote de no saltar partes críticas de la lógica:

    settings.py y models.py: Configuración del usuario personalizado (AUTH_USER_MODEL) y los modelos de asistencia con sus relaciones.

    admin.py: Configuración para ver los registros organizados en el panel de administración nativo de Django.

    views.py: Las vistas basadas en clases para el Dashboard del empleado y el procesamiento del marcado (guardando IP y estados).

    templates/: Estructura de carpetas con base.html, login.html, dashboard.html (con el reloj y botones de marcado).