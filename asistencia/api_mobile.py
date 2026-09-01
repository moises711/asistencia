from __future__ import annotations

import json
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from .models import (
    AusenciaProgramada,
    ConfiguracionGPS,
    CustomUser,
    DispositivoToken,
    RegistroAsistencia,
)
from .utils import calcular_horas_netas, obtener_ip_cliente, validar_ubicacion_gps
from .views import (
    HORAS_SEMANA_MAXIMAS,
    HORAS_SEMANA_MINIMAS,
    calcular_tardanza_y_temprano,
    obtener_recuperacion_pendiente,
    requiere_validacion_gps,
    validar_dia_sin_permiso_ni_feriado,
    validar_gps_para_marcacion,
    validar_horario_para_marcacion,
)


def _cors(response: JsonResponse) -> JsonResponse:
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Api-Token"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def _json(payload: dict, status: int = 200) -> JsonResponse:
    return _cors(JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False}))


def _error(message: str, status: int = 400) -> JsonResponse:
    return _json({"status": "error", "message": message}, status=status)


def _leer_json(request) -> dict:
    if not request.body:
        return {}
    try:
        datos = json.loads(request.body)
        return datos if isinstance(datos, dict) else {}
    except json.JSONDecodeError:
        return {}


def _token_desde_request(request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return (request.headers.get("X-Api-Token") or "").strip()


def _usuario_por_token(request) -> CustomUser | None:
    key = _token_desde_request(request)
    if not key:
        return None
    token = (
        DispositivoToken.objects.select_related("usuario", "usuario__horario", "usuario__area")
        .filter(key=key)
        .first()
    )
    if not token or not token.usuario.is_active:
        return None
    token.save(update_fields=["ultimo_uso"])
    return token.usuario


def _fmt_dt(valor):
    if not valor:
        return None
    local = timezone.localtime(valor) if timezone.is_aware(valor) else valor
    return local.isoformat()


def _fmt_time(valor):
    return valor.strftime("%H:%M") if valor else None


def _td_format(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"


def _serializar_usuario(usuario: CustomUser) -> dict:
    return {
        "id": usuario.id,
        "username": usuario.username,
        "nombre": usuario.get_full_name() or usuario.username,
        "rol": usuario.rol,
        "dni": usuario.dni,
        "area": usuario.area.nombre if usuario.area else None,
        "codigo_qr": usuario.codigo_qr,
        "permite_remoto": usuario.permite_remoto,
        "rol_display": usuario.get_rol_display(),
        "es_rrhh": usuario.rol in (CustomUser.ROL_RRHH, CustomUser.ROL_ADMIN),
    }


def _serializar_registro(registro: RegistroAsistencia | None) -> dict | None:
    if not registro:
        return None
    return {
        "id": registro.id,
        "fecha": registro.fecha.isoformat(),
        "hora_entrada": _fmt_dt(registro.hora_entrada),
        "hora_salida": _fmt_dt(registro.hora_salida),
        "inicio_almuerzo": _fmt_dt(registro.inicio_almuerzo),
        "fin_almuerzo": _fmt_dt(registro.fin_almuerzo),
        "estado": registro.estado,
        "estado_display": registro.get_estado_display(),
        "tipo_entrada": registro.tipo_entrada,
        "tipo_salida": registro.tipo_salida,
        "minutos_tarde": registro.minutos_tarde,
        "actividad_diaria": registro.actividad_diaria,
        "horas_netas": str(registro.horas_netas_trabajadas) if registro.horas_netas_trabajadas else None,
    }


def _proxima_accion(registro: RegistroAsistencia | None) -> str:
    if not registro or not registro.hora_entrada:
        return "entrada"
    if not registro.inicio_almuerzo:
        return "inicio_almuerzo"
    if not registro.fin_almuerzo:
        return "fin_almuerzo"
    if not registro.hora_salida:
        return "salida"
    return "completado"


def _dashboard_payload(usuario: CustomUser) -> dict:
    hoy = timezone.localdate()
    registro_hoy = RegistroAsistencia.objects.filter(empleado=usuario, fecha=hoy).first()
    ultimos = RegistroAsistencia.objects.filter(empleado=usuario).order_by("-fecha")[:5]
    horario = usuario.horario
    config_gps = ConfiguracionGPS.obtener_configuracion_activa()

    inicio_semana = hoy - timedelta(days=hoy.weekday())
    total_horas_semana = RegistroAsistencia.objects.filter(
        empleado=usuario,
        fecha__range=(inicio_semana, hoy),
        horas_netas_trabajadas__isnull=False,
    ).aggregate(total=Sum("horas_netas_trabajadas"))["total"] or timedelta(0)
    horas_restantes = max(timedelta(0), HORAS_SEMANA_MINIMAS - total_horas_semana)
    horas_excedentes = max(timedelta(0), total_horas_semana - HORAS_SEMANA_MAXIMAS)
    if total_horas_semana < HORAS_SEMANA_MINIMAS:
        estado_horas = "Por debajo del mínimo (24 h)"
    elif total_horas_semana > HORAS_SEMANA_MAXIMAS:
        estado_horas = "Supera el máximo (30 h)"
    else:
        estado_horas = "Dentro del rango (24-30 h)"

    minutos_para_tardanza = None
    if horario and not (registro_hoy and registro_hoy.hora_entrada):
        ahora = timezone.localtime(timezone.now()).time()
        from datetime import datetime

        limite = horario.hora_entrada_con_tolerancia()
        diff = (datetime.combine(hoy, limite) - datetime.combine(hoy, ahora)).total_seconds() / 60.0
        if diff > 0:
            minutos_para_tardanza = int(diff)

    permisos = AusenciaProgramada.objects.filter(empleado=usuario).order_by("-creada_en")[:8]

    return {
        "status": "ok",
        "servidor_ahora": timezone.localtime(timezone.now()).isoformat(),
        "user": _serializar_usuario(usuario),
        "horario": None
        if not horario
        else {
            "nombre": horario.nombre,
            "tipo_horario": horario.tipo_horario,
            "hora_entrada": _fmt_time(horario.hora_entrada),
            "hora_salida": _fmt_time(horario.hora_salida),
            "tolerancia_minutos": horario.tolerancia_minutos,
            "dia_laborable": horario.es_laborable(hoy),
            "lunes": horario.lunes,
            "martes": horario.martes,
            "miercoles": horario.miercoles,
            "jueves": horario.jueves,
            "viernes": horario.viernes,
            "sabado": horario.sabado,
            "domingo": horario.domingo,
        },
        "registro_hoy": _serializar_registro(registro_hoy),
        "proxima_accion": _proxima_accion(registro_hoy),
        "requiere_gps": requiere_validacion_gps(usuario),
        "requiere_actividad_salida": usuario.rol in (CustomUser.ROL_PPHH, CustomUser.ROL_EMPLEADO),
        "minutos_para_tardanza": minutos_para_tardanza,
        "config_gps": None
        if not config_gps
        else {
            "nombre": config_gps.nombre,
            "latitud": float(config_gps.latitud),
            "longitud": float(config_gps.longitud),
            "radio": config_gps.radio_permitido_metros,
        },
        "horas_semana": {
            "trabajadas": _td_format(total_horas_semana),
            "restantes": _td_format(horas_restantes),
            "excedentes": _td_format(horas_excedentes),
            "estado": estado_horas,
        },
        "ultimos_registros": [_serializar_registro(r) for r in ultimos],
        "permisos": [
            {
                "id": p.id,
                "fecha_inicio": p.fecha_inicio.isoformat(),
                "fecha_fin": p.fecha_fin.isoformat(),
                "motivo": p.motivo,
                "estado": p.estado,
                "estado_display": p.get_estado_display(),
            }
            for p in permisos
        ],
    }


def _ejecutar_marcacion(usuario: CustomUser, accion: str, payload: dict, ip_empleado: str) -> JsonResponse:
    fecha = timezone.localdate()
    ahora = timezone.localtime(timezone.now())
    registro, _ = RegistroAsistencia.objects.get_or_create(
        empleado=usuario,
        fecha=fecha,
        defaults={"ip_registro": ip_empleado},
    )

    latitud = payload.get("latitud")
    longitud = payload.get("longitud")
    precision = payload.get("precisión", payload.get("precision"))
    tipo_marcacion = payload.get("tipo_marcacion")

    if accion == "entrada":
        for validar in (validar_dia_sin_permiso_ni_feriado, validar_horario_para_marcacion):
            mensaje = validar(usuario, fecha)
            if mensaje:
                return _error(mensaje)
        if tipo_marcacion != "qr":
            mensaje = validar_gps_para_marcacion(usuario, latitud, longitud)
            if mensaje:
                return _error(mensaje)
        if registro.hora_entrada:
            return _error("Entrada ya registrada.")
        registro.hora_entrada = ahora
        registro.ip_registro = ip_empleado
        if latitud not in (None, "") and longitud not in (None, ""):
            registro.latitud_entrada = latitud
            registro.longitud_entrada = longitud
            registro.precisión_entrada = precision
        if tipo_marcacion == "qr":
            registro.tipo_entrada = "qr"
        elif latitud not in (None, "") and longitud not in (None, ""):
            registro.tipo_entrada = "gps"
        else:
            registro.tipo_entrada = "manual"
        if usuario.horario:
            tarde, temprano = calcular_tardanza_y_temprano(usuario.horario, ahora.time())
            registro.minutos_tarde = tarde
            registro.minutos_temprano = temprano
            if not usuario.horario.es_laborable(fecha):
                registro.estado = (
                    RegistroAsistencia.ESTADO_RECUPERACION
                    if obtener_recuperacion_pendiente(usuario)
                    else RegistroAsistencia.ESTADO_FALTA
                )
            elif tarde > usuario.horario.tolerancia_minutos:
                registro.estado = RegistroAsistencia.ESTADO_TARDANZA
            else:
                registro.estado = RegistroAsistencia.ESTADO_A_TIEMPO
        else:
            registro.estado = RegistroAsistencia.ESTADO_A_TIEMPO
    elif accion == "inicio_almuerzo":
        if not registro.hora_entrada:
            return _error("Registra entrada primero.")
        if registro.inicio_almuerzo:
            return _error("Almuerzo ya iniciado.")
        registro.inicio_almuerzo = ahora
    elif accion == "fin_almuerzo":
        if not registro.inicio_almuerzo:
            return _error("Inicia almuerzo primero.")
        if registro.fin_almuerzo:
            return _error("Almuerzo ya finalizado.")
        registro.fin_almuerzo = ahora
    elif accion == "salida":
        if not registro.hora_entrada:
            return _error("Registra entrada primero.")
        if registro.hora_salida:
            return _error("Salida ya registrada.")
        actividad = str(payload.get("actividad") or "").strip()
        if usuario.rol in (CustomUser.ROL_PPHH, CustomUser.ROL_EMPLEADO) and not actividad:
            return _error("Debes ingresar tu resumen de actividades del día para poder marcar la salida.")
        registro.hora_salida = ahora
        if latitud not in (None, "") and longitud not in (None, ""):
            registro.latitud_salida = latitud
            registro.longitud_salida = longitud
            registro.precisión_salida = precision
        if tipo_marcacion == "qr":
            registro.tipo_salida = "qr"
        elif latitud not in (None, "") and longitud not in (None, ""):
            registro.tipo_salida = "gps"
        else:
            registro.tipo_salida = "manual"
        if actividad:
            registro.actividad_diaria = actividad
        registro.horas_netas_trabajadas = calcular_horas_netas(
            registro.hora_entrada,
            registro.hora_salida,
            registro.inicio_almuerzo,
            registro.fin_almuerzo,
        )
        if registro.estado == RegistroAsistencia.ESTADO_RECUPERACION:
            recuperacion = obtener_recuperacion_pendiente(usuario)
            if recuperacion:
                recuperacion.fecha_recuperacion = fecha
                recuperacion.horas_recuperadas = registro.horas_netas_trabajadas or timedelta(0)
                recuperacion.estado = recuperacion.ESTADO_RECUPERADO
                recuperacion.save(update_fields=["fecha_recuperacion", "horas_recuperadas", "estado"])
    else:
        return _error("Acción no válida.")

    registro.save()
    return _json(
        {
            "status": "ok",
            "message": f"Acción '{accion}' registrada exitosamente",
            "accion": accion,
            "registro_hoy": _serializar_registro(registro),
            "proxima_accion": _proxima_accion(registro),
        }
    )


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_login(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    datos = _leer_json(request)
    username = (datos.get("username") or request.POST.get("username") or "").strip()
    password = datos.get("password") or request.POST.get("password") or ""
    if not username or not password:
        return _error("Usuario y contraseña son obligatorios.")
    usuario = authenticate(request, username=username, password=password)
    if usuario is None or not usuario.is_active:
        return _error("Credenciales inválidas.", 401)
    token = DispositivoToken.objects.create(
        usuario=usuario,
        key=secrets.token_hex(32),
        nombre_dispositivo=str(datos.get("dispositivo") or "")[:120],
    )
    return _json({"status": "ok", "token": token.key, "user": _serializar_usuario(usuario)})


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_logout(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    key = _token_desde_request(request)
    if key:
        DispositivoToken.objects.filter(key=key).delete()
    return _json({"status": "ok", "message": "Sesión cerrada"})


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_dashboard(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    return _json(_dashboard_payload(usuario))


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_validar_gps(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    datos = _leer_json(request)
    latitud = datos.get("latitud")
    longitud = datos.get("longitud")
    precision = datos.get("precisión", datos.get("precision"))
    config_gps = ConfiguracionGPS.obtener_configuracion_activa()
    if (latitud in (None, "", 0) and longitud in (None, "", 0)):
        if not config_gps:
            return _json({"config": None, "mensaje": "No hay configuración GPS disponible"})
        return _json(
            {
                "config": {
                    "nombre": config_gps.nombre,
                    "latitud": float(config_gps.latitud),
                    "longitud": float(config_gps.longitud),
                    "radio": config_gps.radio_permitido_metros,
                }
            }
        )
    if not config_gps:
        return _error("Configuración de ubicación de oficina no disponible", 500)
    resultado = validar_ubicacion_gps(
        latitud,
        longitud,
        config_gps.latitud,
        config_gps.longitud,
        config_gps.radio_permitido_metros,
    )
    return _json(
        {
            "valido": resultado["valido"],
            "distancia": resultado["distancia"],
            "mensaje": resultado["mensaje"],
            "precision": precision,
            "radio_permitido": config_gps.radio_permitido_metros,
        }
    )


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_validar_qr_oficina(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    from django.core import signing
    from .views import OFICINA_QR_SALT

    datos = _leer_json(request)
    codigo_qr = str(datos.get("codigo_qr") or "").strip()
    if not codigo_qr:
        return _error("Código QR requerido")
    config_gps = ConfiguracionGPS.obtener_configuracion_activa()
    if not config_gps:
        return _error("No hay configuración GPS activa", 404)
    try:
        payload = signing.loads(codigo_qr, salt=OFICINA_QR_SALT)
    except signing.BadSignature:
        return _error("QR de oficina inválido o alterado")
    if int(payload.get("config_id", 0)) != config_gps.id:
        return _error("El QR no corresponde a la oficina activa")
    return _json({"valido": True, "mensaje": "QR de oficina válido"})


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_marcar(request, accion: str):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    payload = _leer_json(request)
    if not payload:
        payload = {k: request.POST.get(k) for k in request.POST.keys()}
    return _ejecutar_marcacion(usuario, accion, payload, obtener_ip_cliente(request))


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_solicitar_permiso(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    from datetime import datetime

    datos = _leer_json(request)
    fecha_inicio = datos.get("fecha_inicio") or request.POST.get("fecha_inicio")
    fecha_fin = datos.get("fecha_fin") or request.POST.get("fecha_fin")
    motivo = datos.get("motivo") or request.POST.get("motivo")
    if not fecha_inicio or not fecha_fin or not motivo:
        return _error("Faltan datos obligatorios")
    try:
        f_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        f_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return _error("Formato de fecha inválido")
    if f_inicio > f_fin:
        return _error("La fecha de inicio no puede ser mayor que la de fin")
    AusenciaProgramada.objects.create(
        empleado=usuario,
        fecha_inicio=f_inicio,
        fecha_fin=f_fin,
        motivo=motivo,
        estado=AusenciaProgramada.ESTADO_PENDIENTE,
        creada_por=usuario,
    )
    return _json({"status": "ok", "message": "Solicitud enviada correctamente. Espera la aprobación de RRHH."})


def _es_staff_rrhh(usuario: CustomUser) -> bool:
    return usuario.rol in (CustomUser.ROL_RRHH, CustomUser.ROL_ADMIN)


def _serializar_permiso(permiso: AusenciaProgramada) -> dict:
    return {
        "id": permiso.id,
        "empleado_id": permiso.empleado_id,
        "empleado": permiso.empleado.get_full_name() or permiso.empleado.username,
        "area": permiso.empleado.area.nombre if permiso.empleado.area else None,
        "fecha_inicio": permiso.fecha_inicio.isoformat(),
        "fecha_fin": permiso.fecha_fin.isoformat(),
        "motivo": permiso.motivo,
        "estado": permiso.estado,
        "estado_display": permiso.get_estado_display(),
        "dia_completo": permiso.fecha_inicio == permiso.fecha_fin,
    }


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_listar_permisos(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    estado = (request.GET.get("estado") or "").strip()
    qs = AusenciaProgramada.objects.filter(empleado=usuario).select_related("empleado", "empleado__area").order_by("-creada_en")
    if estado:
        qs = qs.filter(estado=estado)
    return _json({"status": "ok", "permisos": [_serializar_permiso(p) for p in qs[:40]]})


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_rrhh_resumen(request):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    if not _es_staff_rrhh(usuario):
        return _error("No tienes permiso de RRHH.", 403)
    hoy = timezone.localdate()
    empleados = CustomUser.objects.filter(
        is_active=True,
        rol__in=[CustomUser.ROL_EMPLEADO, CustomUser.ROL_PPHH],
    ).select_related("area", "horario")
    registros = {r.empleado_id: r for r in RegistroAsistencia.objects.filter(fecha=hoy, empleado__in=empleados)}
    presentes = tardanzas = faltas = 0
    lista = []
    for emp in empleados.order_by("last_name", "first_name", "username"):
        reg = registros.get(emp.id)
        estado = "no_marcado"
        estado_display = "No marcado"
        if reg:
            estado = reg.estado
            estado_display = reg.get_estado_display()
            if reg.estado == RegistroAsistencia.ESTADO_A_TIEMPO:
                presentes += 1
            elif reg.estado == RegistroAsistencia.ESTADO_TARDANZA:
                tardanzas += 1
            elif reg.estado == RegistroAsistencia.ESTADO_FALTA:
                faltas += 1
            elif reg.hora_entrada:
                presentes += 1
        lista.append({
            "id": emp.id,
            "nombre": emp.get_full_name() or emp.username,
            "area": emp.area.nombre if emp.area else None,
            "estado": estado,
            "estado_display": estado_display,
            "hora_entrada": _fmt_dt(reg.hora_entrada) if reg else None,
            "hora_salida": _fmt_dt(reg.hora_salida) if reg else None,
        })
    pendientes = (
        AusenciaProgramada.objects.filter(estado=AusenciaProgramada.ESTADO_PENDIENTE)
        .select_related("empleado", "empleado__area")
        .order_by("-creada_en")[:20]
    )
    return _json({
        "status": "ok",
        "kpis": {
            "empleados": empleados.count(),
            "presentes": presentes,
            "tardanzas": tardanzas,
            "faltas": faltas,
            "no_marcados": empleados.count() - presentes - tardanzas - faltas,
        },
        "asistencias_hoy": lista,
        "permisos_pendientes": [_serializar_permiso(p) for p in pendientes],
    })


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_rrhh_procesar_permiso(request, permiso_id: int):
    if request.method == "OPTIONS":
        return _cors(JsonResponse({}))
    usuario = _usuario_por_token(request)
    if not usuario:
        return _error("No autenticado.", 401)
    if not _es_staff_rrhh(usuario):
        return _error("No tienes permiso de RRHH.", 403)
    datos = _leer_json(request)
    accion = (datos.get("accion") or "").strip().lower()
    permiso = AusenciaProgramada.objects.select_related("empleado").filter(pk=permiso_id).first()
    if not permiso:
        return _error("Solicitud no encontrada.", 404)
    if accion == "aprobar":
        permiso.estado = AusenciaProgramada.ESTADO_APROBADA
    elif accion == "rechazar":
        permiso.estado = AusenciaProgramada.ESTADO_RECHAZADA
    else:
        return _error("Acción no válida.")
    permiso.procesada_por = usuario
    permiso.save(update_fields=["estado", "procesada_por"])
    return _json({
        "status": "ok",
        "message": f"Solicitud {permiso.get_estado_display().lower()}",
        "permiso": _serializar_permiso(permiso),
    })

