from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path("login/", views.CustomLoginView.as_view(template_name="asistencia/login.html"), name="login"),
    path("logout/", views.LogoutView.as_view(next_page="login"), name="logout"),

    # Registration (if needed)
    path("register/", views.RegisterView.as_view(), name="register"),
    
    # Dashboard roles
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("panel-control/", views.PanelControlView.as_view(), name="panel_control"),
    path("admin-dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    
    # Marcar asistencia
    path("marcar/<str:accion>/", views.marcar_evento, name="marcar_evento"),
    path("validar-gps/", views.validar_gps, name="validar_gps"),
    path("validar-qr-oficina/", views.validar_qr_oficina, name="validar_qr_oficina"),
    path("capturar-gps/", views.capturar_gps_admin, name="capturar_gps_admin"),
    path("guardar-gps/", views.guardar_gps_admin, name="guardar_gps_admin"),
    path("qr-oficina/descargar/", views.descargar_qr_oficina, name="descargar_qr_oficina"),
    
    # Escaneo QR para RRHH
    path("api/escanear-qr/", views.escanear_qr_empleado, name="escanear_qr_empleado"),
    
    # Vistas de Admin
    path("empleados/", views.EmpleadosView.as_view(), name="empleados"),
    path("empleados/<int:empleado_id>/eliminar/", views.eliminar_empleado, name="eliminar_empleado"),
    path("config-ip/", views.ConfigIpView.as_view(), name="config_ip"),
    path("autorizar-ip/", views.autorizar_ip_actual, name="autorizar_ip"),
    
    # API endpoints
    path("api/empleado/<int:empleado_id>/actualizar/", views.actualizar_empleado_api, name="actualizar_empleado_api"),
    
    # Reportes y justificaciones
    path("asistencias/reporte/", views.ReporteAsistenciasView.as_view(), name="reporte"),
    path("asistencias/reporte/excel/", views.exportar_reporte_excel, name="exportar_reporte_excel"),
    path("justificaciones/pendientes/", views.JustificacionesPendientesView.as_view(), name="justificaciones_pendientes"),
    path("justificaciones/procesar/<int:justificacion_id>/", views.procesar_justificacion, name="procesar_justificacion"),
    path("asistencias/<int:asistencia_id>/justificar/", views.JustificacionCreateView.as_view(), name="crear_justificacion"),
    
    # Areas y horarios
    path("areas/", views.AreasView.as_view(), name="areas"),
    path("horarios/", views.HorariosView.as_view(), name="horarios"),
    path("feriados/crear/", views.crear_feriado, name="crear_feriado"),
    path("feriados/<int:feriado_id>/eliminar/", views.eliminar_feriado, name="eliminar_feriado"),
    path("ausencias/crear/", views.crear_ausencia_programada, name="crear_ausencia_programada"),
    path("ausencias/<int:ausencia_id>/procesar/", views.procesar_ausencia, name="procesar_ausencia"),
    path("api/horario/<int:horario_id>/actualizar/", views.actualizar_horario_api, name="actualizar_horario_api"),
    path("api/area/<int:area_id>/actualizar/", views.actualizar_area_api, name="actualizar_area_api"),
    
    # Actividades de empleados (Admin)
    path("actividades/", views.ActividadesEmpleadosView.as_view(), name="actividades_empleados"),

    # Credenciales de acceso del usuario autenticado
    path("credenciales/", views.CredencialesAccesoView.as_view(), name="credenciales_acceso"),

    # Cambio de contraseña (usuario actual)
    path('password/change/', views.RoleAwarePasswordChangeView.as_view(template_name='asistencia/password_change.html'), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='asistencia/password_change_done.html'), name='password_change_done'),

    # Recuperación de contraseña (olvido)
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]
