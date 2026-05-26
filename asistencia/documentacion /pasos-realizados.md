# Pasos Realizados

Este documento lista cada tarea del roadmap y requerimientos, marcando su estado y describiendo brevemente como se realizo. El estado se basa en lo que existe actualmente en el repositorio.

---

## Estado actual verificado

- [x] **Proyecto Django base creado**
  - Existe `manage.py` y la carpeta del proyecto `control_asistencia/` con `settings.py`, `urls.py`, `asgi.py` y `wsgi.py`.

- [x] **App asistencia creada**
  - Se creo la carpeta `asistencia/` con `models.py`, `views.py`, `admin.py`, `urls.py`, `forms.py` y templates.

---

## Fase 1: Configuracion Inicial y Modelo de Usuarios

- [x] **Inicializar el proyecto Django**
  - El proyecto base ya esta creado (estructura Django inicial).

- [x] **Crear la app asistencia**
  - La app existe y esta registrada en `INSTALLED_APPS`.

- [x] **Configurar settings.py (Base de datos, zona horaria, AUTH_USER_MODEL)**
  - Se configuro `AUTH_USER_MODEL`, `LANGUAGE_CODE` y `TIME_ZONE`.

- [x] **Escribir el modelo CustomUser y el modelo Horario en models.py**
  - Se definieron los modelos `CustomUser` y `Horario`.

- [ ] **Ejecutar migraciones y crear superuser**
  - Falta ejecutar `makemigrations`, `migrate` y `createsuperuser`.

## Fase 2: Nucleo del Modelo de Datos

- [x] **Modelos secundarios: IpOficinaAutorizada, RegistroAsistencia, Justificacion, AusenciaProgramada, DiaFeriado**
  - Se implementaron todos los modelos requeridos.

- [x] **Registrar modelos en admin.py**
  - Se registraron los modelos para el panel admin.

## Fase 3: Logica del Backend

- [x] **Funciones utilitarias en utils.py**
  - Se agrego `obtener_ip_cliente` y calculo de horas netas.

- [x] **Vistas para Marcar Entrada, Salida, etc.**
  - Se creo la vista `marcar_evento` con acciones de entrada, almuerzo y salida.

- [x] **Validaciones de permisos remotos y IP**
  - Se valida IP autorizada cuando `permite_remoto` es False.

## Fase 4: Interfaz de Usuario (Empleado)

- [x] **Plantilla base con Tailwind CSS**
  - Se creo `base.html` con Tailwind via CDN.

- [x] **Pantalla de login**
  - Se creo `registration/login.html` y ruta `/login/`.

- [x] **Dashboard del empleado con reloj y botones reactivos**
  - Se creo `dashboard.html` con reloj y botones que llaman al backend.

- [x] **Formulario de justificaciones**
  - Se creo `justificacion_form.html` y la vista de creacion.

## Fase 5: Automatizacion y Tareas en Segundo Plano

- [x] **Comando personalizado para verificar faltas**
  - Se creo `management/commands/verificar_faltas.py`.

- [x] **Senales para notificaciones por correo**
  - Se implementaron senales para tardanza y nuevas justificaciones.

## Fase 6: Panel de Control y Reportes

- [x] **Vista de panel-control para RRHH**
  - Se creo `panel_control.html` con indicadores basicos.

- [x] **Tabla de filtrado de asistencias**
  - Se creo `reporte.html` como base (falta el filtro avanzado).

- [ ] **Procesamiento de justificaciones (Aprobar/Rechazar)**
  - Falta implementar la accion de aprobar/rechazar.

- [ ] **Vista de consolidado mensual**
  - Falta la vista con agregaciones del ORM.

## Fase 7: Despliegue y Produccion

- [x] **Pruebas unitarias (tests.py)**
  - Se agregaron tests basicos de horario y tardanza.

- [x] **Proteccion antifraude (timezone.now)**
  - El marcado usa `timezone.now()` en el backend.

- [ ] **django-environ para credenciales**
  - No esta configurado.

- [ ] **WhiteNoise para archivos estaticos**
  - No esta configurado.

- [ ] **Docker y docker-compose**
  - No existen `Dockerfile` ni `docker-compose.yml`.

---

**Nota:** Puedo continuar con las tareas pendientes (migraciones, aprobacion/rechazo, consolidado mensual y despliegue) si lo deseas.
