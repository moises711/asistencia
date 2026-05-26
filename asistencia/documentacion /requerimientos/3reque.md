🗺️ Roadmap de Desarrollo Refinado y Completo (6 Fases Oficiales)
Fase 1: Inicialización, Arquitectura de Datos y Entorno Seguro

    Paso 1.1 (Seguridad desde el inicio): Instalar django-environ. Configurar settings.py para que lea el SECRET_KEY, las credenciales de PostgreSQL y las llaves de correo (SMTP) estrictamente desde un archivo .env.

    Paso 1.2 (Modelos Base): Crear la app asistencia y definir Horario (con días laborables booleanos) y CustomUser.

    Paso 1.3 (Modelos de Excepciones y Control): Crear los modelos IpOficinaAutorizada, RegistroAsistencia (con campo horas_netas_trabajadas), Justificacion, AusenciaProgramada y DiaFeriado.

    Paso 1.4 (Panel de Administración): Configurar admin.py incluyendo formularios personalizados para que RRHH pueda dar de alta empleados y asignarles sus turnos.

Fase 2: Pruebas Unitarias (Testing Automatizado)

    Paso 2.1 (Entorno de Pruebas): Crear el archivo tests.py antes de tocar las vistas.

    Paso 2.2 (Casos de Prueba Críticos): Programar tests automatizados para validar:

        Cálculo de estados: Entrada a tiempo vs. Tardanza (aplicando los minutos de tolerancia).

        Bloqueo por IP: Peticiones desde IPs no registradas deben devolver un código HTTP 403.

        Validación de Excepciones: Verificar que si un usuario tiene permite_remoto=True, el sistema ignore la restricción de IP.

Fase 3: Lógica de Negocio y Protección Antifalsificación (Backend)

    Paso 3.1 (Capa Antifraude de IP): Implementar la función utilitaria para extraer la IP real detrás de proxies (HTTP_X_FORWARDED_FOR de Nginx) y bloquear VPNs comerciales detectadas.

    Paso 3.2 (Capa Antifraude de Tiempo): Diseñar las vistas de marcado (Entrada, Almuerzo, Salida) usando exclusivamente timezone.now() del servidor. El backend rechazará cualquier parámetro de fecha/hora enviado desde el frontend del cliente.

    Paso 3.3 (Cálculo de Horas): Programar la lógica que resta automáticamente el tiempo transcurrido entre inicio_almuerzo y fin_almuerzo al momento de calcular las horas netas de salida.

Fase 4: Automatización de Tareas (Celery) y Notificaciones

    Paso 4.1 (Infraestructura Celery): Configurar Celery con Redis como Broker en el proyecto Django (celery.py).

    Paso 4.2 (Tarea Programada de Faltas - Celery Beat): Crear la tarea diaria que corre a las 11:00 AM. Su lógica debe ser:

        Filtrar empleados activos cuyo horario indique que hoy es su día laborable.

        Excluir a los que tengan un registro en AusenciaProgramada (vacaciones/licencia aprobada) o si la fecha coincide con un DiaFeriado.

        A los restantes que no tengan marcado de entrada, registrarles automáticamente el estado 'falta'.

    Paso 4.3 (Señales de Alerta por Correo): Usar django.db.models.signals.post_save para enviar correos electrónicos automáticos (vía el SMTP configurado en el .env) cuando se registre una tardanza o se cree una nueva solicitud de justificación.

Fase 5: Interfaz de Usuario (Frontend Responsivo)

    Paso 5.1 (Dashboard del Empleado): Crear una interfaz móvil-friendly con Tailwind CSS. Incluir un reloj en tiempo real mediante JavaScript. Los botones de marcado deben actualizarse dinámicamente usando fetch() de JavaScript para interactuar con el backend sin recargar la página.

    Paso 5.2 (Módulo de Gestión de Vacaciones y Justificaciones): Diseñar los formularios web para que el empleado solicite vacaciones o justifique faltas, y la bandeja del Supervisor para aprobar/rechazar con un clic (AJAX).

    Paso 5.3 (Consolidado Mensual para RRHH): Vista con filtros de fecha que use agregaciones del ORM de Django (Sum, Count) para entregar el total de horas trabajadas y minutos de tardanza por empleado de forma masiva.

Fase 6: Preparación para Producción, Docker y Documentación

    Paso 6.1 (Archivos Estáticos): Instalar y configurar WhiteNoise en los middlewares de Django para el servicio eficiente de archivos CSS/JS en producción sin depender de Nginx para los estáticos.

    Paso 6.2 (Contenedorización): Escribir el Dockerfile (multi-stage para optimizar peso) y un docker-compose.yml que levante tres contenedores conectados: la app Django (Gunicorn), la base de datos PostgreSQL y el worker/beat de Celery junto a Redis.

    Paso 6.3 (Documentación Técnica y Manuales): * Generar un archivo README.md detallando los comandos de instalación, variables del .env requeridas y cómo ejecutar los tests.

        Escribir un documento anexo de Manual de Usuario que explique visualmente a los supervisores cómo actualizar la IP de la oficina en caso de que su internet sea dinámico.