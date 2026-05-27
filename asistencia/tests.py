import json
from datetime import datetime, time, date, timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import (
    AusenciaProgramada,
    ConfiguracionGPS,
    CustomUser,
    DiaFeriado,
    Horario,
    IpOficinaAutorizada,
    RegistroAsistencia,
    RecuperacionDia,
    Area,
)


class HorarioTests(TestCase):
    def test_hora_entrada_con_tolerancia(self):
        horario = Horario.objects.create(
            nombre="Horario Base",
            hora_entrada=time(9, 0),
            hora_salida=time(18, 0),
            tolerancia_minutos=10,
        )
        self.assertEqual(horario.hora_entrada_con_tolerancia(), time(9, 10))


class RegistroAsistenciaTests(TestCase):
    def setUp(self):
        self.horario = Horario.objects.create(
            nombre="Horario Base",
            hora_entrada=time(9, 0),
            hora_salida=time(18, 0),
            tolerancia_minutos=5,
        )
        self.usuario = CustomUser.objects.create_user(
            username="empleado",
            password="test1234",
            dni="12345678",
            rol=CustomUser.ROL_EMPLEADO,
            horario=self.horario,
        )

    def _simular_entrada(self, hora_actual, fecha=date(2026, 5, 26)):
        """
        Replica exactamente la lógica de marcar_evento (views.py línea 564):
            if usuario.horario and ahora.time() > usuario.horario.hora_entrada_con_tolerancia():
                registro.estado = ESTADO_TARDANZA
            else:
                registro.estado = ESTADO_A_TIEMPO
        """
        ahora = timezone.make_aware(datetime.combine(fecha, hora_actual))
        registro = RegistroAsistencia.objects.create(
            empleado=self.usuario,
            fecha=fecha,
            hora_entrada=ahora,
        )
        if self.usuario.horario and ahora.time() > self.usuario.horario.hora_entrada_con_tolerancia():
            registro.estado = RegistroAsistencia.ESTADO_TARDANZA
        else:
            registro.estado = RegistroAsistencia.ESTADO_A_TIEMPO
        registro.save()
        return registro

    def test_entrada_exactamente_en_limite__puntual(self):
        """09:05:00 == límite → Puntual (NO es mayor, sólo igual)"""
        # Horario: 09:00, tolerancia: 5 min → límite = 09:05:00
        registro = self._simular_entrada(time(9, 5, 0))
        self.assertEqual(
            registro.estado,
            RegistroAsistencia.ESTADO_A_TIEMPO,
            "Marcar a las 09:05:00 (igual al límite) debe ser PUNTUAL"
        )

    def test_entrada_un_segundo_tarde__tardanza(self):
        """09:05:01 > límite → Tardanza"""
        registro = self._simular_entrada(time(9, 5, 1))
        self.assertEqual(
            registro.estado,
            RegistroAsistencia.ESTADO_TARDANZA,
            "Marcar a las 09:05:01 (1 seg después del límite) debe ser TARDANZA"
        )

    def test_entrada_antes_del_limite__puntual(self):
        """09:04:59 < límite → Puntual"""
        registro = self._simular_entrada(time(9, 4, 59))
        self.assertEqual(
            registro.estado,
            RegistroAsistencia.ESTADO_A_TIEMPO,
            "Marcar a las 09:04:59 (antes del límite) debe ser PUNTUAL"
        )

    def test_entrada_hora_entrada_exacta__puntual(self):
        """09:00:00 (antes de la tolerancia) → Puntual"""
        registro = self._simular_entrada(time(9, 0, 0))
        self.assertEqual(
            registro.estado,
            RegistroAsistencia.ESTADO_A_TIEMPO,
            "Marcar a las 09:00:00 (hora exacta de entrada) debe ser PUNTUAL"
        )

    def test_entrada_muy_tarde__tardanza(self):
        """10:00:00 (muy tarde) → Tardanza"""
        registro = self._simular_entrada(time(10, 0, 0))
        self.assertEqual(
            registro.estado,
            RegistroAsistencia.ESTADO_TARDANZA,
            "Marcar a las 10:00:00 debe ser TARDANZA"
        )




class ExportarExcelTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin_user",
            password="test1234",
            dni="87654321",
            rol=CustomUser.ROL_ADMIN,
        )
        self.empleado = CustomUser.objects.create_user(
            username="empleado_user",
            password="test1234",
            dni="12345678",
            rol=CustomUser.ROL_EMPLEADO,
        )
        
    def test_exportar_excel_unauthorized(self):
        self.client.login(username="empleado_user", password="test1234")
        response = self.client.get("/asistencias/reporte/excel/")
        self.assertEqual(response.status_code, 403)
        
    def test_exportar_excel_authorized(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.get("/asistencias/reporte/excel/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="Reporte_Asistencias_'))


class RRHHAndPermissionsTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin_user",
            password="test1234",
            dni="87654321",
            rol=CustomUser.ROL_ADMIN,
        )
        self.rrhh = CustomUser.objects.create_user(
            username="rrhh_user",
            password="test1234",
            dni="98765432",
            rol=CustomUser.ROL_RRHH,
        )
        self.horario = Horario.objects.create(
            nombre="Turno mañana",
            hora_entrada=time(8, 0),
            hora_salida=time(17, 0),
            tolerancia_minutos=15,
        )
        self.empleado = CustomUser.objects.create_user(
            username="empleado_user",
            password="test1234",
            dni="12345678",
            rol=CustomUser.ROL_EMPLEADO,
            horario=self.horario,
        )

    def test_rrhh_accede_a_empleados_y_no_admin_dashboard(self):
        self.client.login(username="rrhh_user", password="test1234")
        response = self.client.get("/empleados/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/admin-dashboard/")
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, {302, 403})

        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_rrhh_puede_marcar_salida_sin_descripcion(self):
        self.rrhh.permite_remoto = True
        self.rrhh.save(update_fields=["permite_remoto"])
        self.client.login(username="rrhh_user", password="test1234")
        fecha = date(2026, 5, 27)
        RegistroAsistencia.objects.create(
            empleado=self.rrhh,
            fecha=fecha,
            hora_entrada=timezone.make_aware(datetime.combine(fecha, time(9, 0))),
            estado=RegistroAsistencia.ESTADO_A_TIEMPO,
        )

        with patch("asistencia.views.timezone.localdate", return_value=fecha), patch(
            "asistencia.views.timezone.now",
            return_value=timezone.make_aware(datetime.combine(fecha, time(18, 0))),
        ):
            response = self.client.post("/marcar/salida/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse("resumen de actividades" in response.content.decode("utf-8").lower())

    def test_dashboard_rrhh_no_muestra_exigencia_de_actividad(self):
        self.client.login(username="rrhh_user", password="test1234")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Resumen de Actividades del Día")

    def test_rrhh_no_puede_asignar_rol_admin(self):
        self.client.login(username="rrhh_user", password="test1234")
        response = self.client.post(
            f"/api/empleado/{self.empleado.id}/actualizar/",
            data='{"rol": "admin"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.rol, CustomUser.ROL_EMPLEADO)

    def test_rrhh_puede_eliminar_empleado(self):
        self.client.login(username="rrhh_user", password="test1234")
        empleado2 = CustomUser.objects.create_user(
            username="empleado2",
            password="test1234",
            dni="23456789",
            rol=CustomUser.ROL_EMPLEADO,
        )
        response = self.client.post(f"/empleados/{empleado2.id}/eliminar/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(pk=empleado2.id).exists())

    def test_rrhh_puede_eliminar_practicante(self):
        self.client.login(username="rrhh_user", password="test1234")
        practicante = CustomUser.objects.create_user(
            username="practicante2",
            password="test1234",
            dni="33445566",
            rol=CustomUser.ROL_PPHH,
        )
        response = self.client.post(f"/empleados/{practicante.id}/eliminar/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(pk=practicante.id).exists())

    def test_rrhh_no_puede_eliminar_admin(self):
        self.client.login(username="rrhh_user", password="test1234")
        response = self.client.post(f"/empleados/{self.admin.id}/eliminar/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(CustomUser.objects.filter(pk=self.admin.id).exists())

    def test_rrhh_puede_exportar_excel(self):
        self.client.login(username="rrhh_user", password="test1234")
        response = self.client.get("/asistencias/reporte/excel/")
        self.assertEqual(response.status_code, 200)

    def test_formulario_permiso_incluye_practicante(self):
        from .forms import AusenciaProgramadaForm

        practicante = CustomUser.objects.create_user(
            username="practicante_form",
            password="test1234",
            dni="44556677",
            rol=CustomUser.ROL_PPHH,
        )
        form = AusenciaProgramadaForm()
        self.assertIn(practicante, form.fields["empleado"].queryset)
        self.assertIn(self.empleado, form.fields["empleado"].queryset)

    def test_formulario_meta_horas_solo_practicante(self):
        from .forms import MetaHorasPracticanteForm

        practicante = CustomUser.objects.create_user(
            username="practicante_meta",
            password="test1234",
            dni="55667788",
            rol=CustomUser.ROL_PPHH,
        )
        form = MetaHorasPracticanteForm()
        self.assertIn(practicante, form.fields["empleado"].queryset)
        self.assertNotIn(self.empleado, form.fields["empleado"].queryset)

    def test_ausencia_aprobada_no_genera_falta_ni_recuperacion(self):
        self.client.login(username="admin_user", password="test1234")
        hoy = timezone.localdate()
        permiso = AusenciaProgramada.objects.create(
            empleado=self.empleado,
            fecha_inicio=hoy,
            fecha_fin=hoy,
            motivo="Vacaciones",
            estado=AusenciaProgramada.ESTADO_APROBADA,
            creada_por=self.admin,
            procesada_por=self.admin,
        )
        call_command('verificar_faltas')
        self.assertFalse(RegistroAsistencia.objects.filter(empleado=self.empleado, fecha=hoy, estado=RegistroAsistencia.ESTADO_FALTA).exists())
        self.assertFalse(RecuperacionDia.objects.filter(empleado=self.empleado, fecha_falta=hoy).exists())

    def test_verificar_faltas_crea_recuperacion_con_registro_falta(self):
        self.client.login(username="admin_user", password="test1234")
        hoy = timezone.localdate()
        call_command('verificar_faltas')
        falta = RegistroAsistencia.objects.filter(empleado=self.empleado, fecha=hoy, estado=RegistroAsistencia.ESTADO_FALTA).first()
        self.assertIsNotNone(falta)
        recuperacion = RecuperacionDia.objects.filter(empleado=self.empleado, fecha_falta=hoy).first()
        self.assertIsNotNone(recuperacion)
        self.assertEqual(recuperacion.registro_falta, falta)


class HolidayAndApiTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin_user",
            password="test1234",
            dni="87654321",
            rol=CustomUser.ROL_ADMIN,
        )
        self.empleado = CustomUser.objects.create_user(
            username="empleado_user",
            password="test1234",
            dni="12345678",
            rol=CustomUser.ROL_EMPLEADO,
        )
        self.area = Area.objects.create(nombre="Sistemas", descripcion="Área de TI")
        self.horario = Horario.objects.create(
            nombre="Turno mañana",
            hora_entrada=time(8, 0),
            hora_salida=time(17, 0),
            tolerancia_minutos=15
        )

    def test_crear_y_eliminar_feriado(self):
        self.client.login(username="admin_user", password="test1234")
        # Crear feriado
        response = self.client.post("/feriados/crear/", {
            "fecha": "2026-12-25",
            "descripcion": "Navidad"
        })
        self.assertEqual(response.status_code, 302)
        feriado = DiaFeriado.objects.get(fecha="2026-12-25")
        self.assertEqual(feriado.descripcion, "Navidad")

        # Eliminar feriado
        response = self.client.post(f"/feriados/{feriado.id}/eliminar/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(DiaFeriado.objects.filter(id=feriado.id).exists())

    def test_actualizar_area_api(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post(
            f"/api/area/{self.area.id}/actualizar/",
            data='{"nombre": "Sistemas Modificado", "descripcion": "Nueva TI"}',
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.area.refresh_from_db()
        self.assertEqual(self.area.nombre, "Sistemas Modificado")
        self.assertEqual(self.area.descripcion, "Nueva TI")

    def test_actualizar_horario_api(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post(
            f"/api/horario/{self.horario.id}/actualizar/",
            data='{"nombre": "Horario Especial", "hora_entrada": "07:30:00", "hora_salida": "16:30:00", "lunes": true}',
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.horario.refresh_from_db()
        self.assertEqual(self.horario.nombre, "Horario Especial")
        self.assertEqual(self.horario.hora_entrada, time(7, 30))
        self.assertTrue(self.horario.lunes)

    def test_actualizar_empleado_api_rechaza_rol_invalido(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post(
            f"/api/empleado/{self.empleado.id}/actualizar/",
            data='{"email": "empleado@demo.com", "rol": "gerente"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.rol, CustomUser.ROL_EMPLEADO)

    def test_actualizar_empleado_api_acepta_rol_rrhh(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post(
            f"/api/empleado/{self.empleado.id}/actualizar/",
            data='{"email": "empleado@demo.com", "rol": "rrhh"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.rol, CustomUser.ROL_RRHH)

    def test_actualizar_empleado_api_cambia_contrasena(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post(
            f"/api/empleado/{self.empleado.id}/actualizar/",
            data='{"password1": "NuevaClave123!", "password2": "NuevaClave123!"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.empleado.refresh_from_db()
        self.assertTrue(self.empleado.check_password("NuevaClave123!"))

    def test_actualizar_empleado_api_campos_completos(self):
        self.client.login(username="admin_user", password="test1234")
        payload = (
            '{"first_name": "Juan", "last_name": "Perez", "username": "jperez", '
            f'"email": "juan@demo.com", "dni": "11111111", "area": {self.area.id}, '
            '"rol": "empleado", "permite_remoto": true}'
        )
        response = self.client.post(
            f"/api/empleado/{self.empleado.id}/actualizar/",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.first_name, "Juan")
        self.assertEqual(self.empleado.last_name, "Perez")
        self.assertEqual(self.empleado.username, "jperez")
        self.assertEqual(self.empleado.email, "juan@demo.com")
        self.assertTrue(self.empleado.permite_remoto)

    def test_actualizar_empleado_api_actualiza_horario(self):
        self.client.login(username="admin_user", password="test1234")
        nuevo_horario = Horario.objects.create(
            nombre="Turno tarde",
            hora_entrada=time(13, 0),
            hora_salida=time(21, 0),
            tolerancia_minutos=10,
        )
        response = self.client.post(
            f"/api/empleado/{self.empleado.id}/actualizar/",
            data=json.dumps({
                "horario": nuevo_horario.id,
                "rol": "empleado",
                "email": "empleado@demo.com",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.horario, nuevo_horario)

    def test_actualizar_empleado_api_rechaza_email_invalido(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post(
            f"/api/empleado/{self.empleado.id}/actualizar/",
            data='{"email": "correo-invalido", "rol": "empleado"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_actualizar_horario_api_parsea_booleanos_de_cadena(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post(
            f"/api/horario/{self.horario.id}/actualizar/",
            data='{"lunes": "false", "martes": "true"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.horario.refresh_from_db()
        self.assertFalse(self.horario.lunes)
        self.assertTrue(self.horario.martes)

    def test_crear_permiso_programado(self):
        self.client.login(username="admin_user", password="test1234")
        response = self.client.post("/ausencias/crear/", {
            "empleado": self.empleado.id,
            "fecha_inicio": "2026-06-15",
            "fecha_fin": "2026-06-17",
            "motivo": "Capacitación externa",
        })
        self.assertEqual(response.status_code, 302)
        from .models import AusenciaProgramada
        ausencia = AusenciaProgramada.objects.get(empleado=self.empleado, fecha_inicio="2026-06-15")
        self.assertEqual(ausencia.estado, AusenciaProgramada.ESTADO_PENDIENTE)
        self.assertIsNone(ausencia.procesada_por)

    def test_procesar_permiso_programado(self):
        self.client.login(username="admin_user", password="test1234")
        from .models import AusenciaProgramada
        ausencia = AusenciaProgramada.objects.create(
            empleado=self.empleado,
            fecha_inicio=date(2026, 6, 15),
            fecha_fin=date(2026, 6, 16),
            motivo="Asunto personal",
            estado=AusenciaProgramada.ESTADO_PENDIENTE,
        )
        response = self.client.post(f"/ausencias/{ausencia.id}/procesar/", {"accion": "aprobar"})
        self.assertEqual(response.status_code, 302)
        ausencia.refresh_from_db()
        self.assertEqual(ausencia.estado, AusenciaProgramada.ESTADO_APROBADA)
        self.assertEqual(ausencia.procesada_por, self.admin)

    def test_verificar_faltas_no_genera_falta_en_feriado(self):
        from .models import DiaFeriado
        DiaFeriado.objects.create(fecha=date(2026, 6, 18), descripcion="Feriado Test")
        with patch("asistencia.management.commands.verificar_faltas.timezone.localdate", return_value=date(2026, 6, 18)):
            out = StringIO()
            call_command("verificar_faltas", stdout=out)
            self.assertIn("Dia feriado", out.getvalue())

    def test_verificar_faltas_respecta_permiso_aprobado(self):
        from .models import AusenciaProgramada
        AusenciaProgramada.objects.create(
            empleado=self.empleado,
            fecha_inicio=date(2026, 6, 18),
            fecha_fin=date(2026, 6, 18),
            motivo="Entrenamiento",
            estado=AusenciaProgramada.ESTADO_APROBADA,
        )
        with patch("asistencia.management.commands.verificar_faltas.timezone.localdate", return_value=date(2026, 6, 18)):
            out = StringIO()
            call_command("verificar_faltas", stdout=out)
            self.assertIn("Faltas creadas: 0", out.getvalue())

    def test_verificar_faltas_crea_recuperacion_dia(self):
        self.empleado.horario = self.horario
        self.empleado.save(update_fields=["horario"])
        with patch("asistencia.management.commands.verificar_faltas.timezone.localdate", return_value=date(2026, 6, 18)):
            out = StringIO()
            call_command("verificar_faltas", stdout=out)
            self.assertIn("Faltas creadas: 1", out.getvalue())
        recuperacion = RecuperacionDia.objects.get(empleado=self.empleado, fecha_falta=date(2026, 6, 18))
        self.assertEqual(recuperacion.horas_a_recuperar, self.horario.duracion_jornada())
        self.assertEqual(recuperacion.estado, RecuperacionDia.ESTADO_PENDIENTE)


class MarcarEntradaValidacionesTests(TestCase):
    def setUp(self):
        ConfiguracionGPS.objects.all().update(activa=False)
        self.config_gps = ConfiguracionGPS.objects.create(
            nombre="Oficina Test",
            latitud=-12.046374,
            longitud=-77.042793,
            radio_permitido_metros=500,
            activa=True,
        )
        self.horario_laborable = Horario.objects.create(
            nombre="Practicante L-V",
            hora_entrada=time(9, 0),
            hora_salida=time(18, 0),
            tolerancia_minutos=10,
            sabado=False,
            domingo=False,
        )
        self.horario_sabado = Horario.objects.create(
            nombre="Solo sabado",
            hora_entrada=time(9, 0),
            hora_salida=time(14, 0),
            tolerancia_minutos=0,
            lunes=False,
            martes=False,
            miercoles=False,
            jueves=False,
            viernes=False,
            sabado=True,
            domingo=False,
        )
        self.empleado = CustomUser.objects.create_user(
            username="practicante1",
            password="test1234",
            dni="99887766",
            rol=CustomUser.ROL_EMPLEADO,
            horario=self.horario_laborable,
            permite_remoto=False,
        )
        IpOficinaAutorizada.objects.create(
            nombre_sede="Test LAN",
            ip_publica="127.0.0.1",
            activa=True,
        )

    def test_entrada_sin_gps_es_rechazada(self):
        self.client.login(username="practicante1", password="test1234")
        response = self.client.post("/marcar/entrada/")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("ubicación", data["message"].lower())

    def test_entrada_sin_horario_es_rechazada(self):
        self.empleado.horario = None
        self.empleado.save(update_fields=["horario"])
        self.client.login(username="practicante1", password="test1234")
        response = self.client.post(
            "/marcar/entrada/",
            {"latitud": "-12.046374", "longitud": "-77.042793"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("horario", response.json()["message"].lower())

    def test_entrada_dia_no_laborable_es_rechazada(self):
        self.empleado.horario = self.horario_sabado
        self.empleado.save(update_fields=["horario"])
        self.client.login(username="practicante1", password="test1234")
        # 2026-05-26 es martes
        with patch("asistencia.views.timezone.localdate", return_value=date(2026, 5, 26)):
            response = self.client.post(
                "/marcar/entrada/",
                {"latitud": "-12.046374", "longitud": "-77.042793"},
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("laborable", response.json()["message"].lower())

    def test_entrada_sabado_recuperacion_pendiente_permitida(self):
        self.empleado.horario = self.horario_sabado
        self.empleado.save(update_fields=["horario"])
        RecuperacionDia.objects.create(
            empleado=self.empleado,
            fecha_falta=date(2026, 5, 25),
            horas_a_recuperar=timedelta(hours=8),
            estado=RecuperacionDia.ESTADO_PENDIENTE,
        )
        self.client.login(username="practicante1", password="test1234")
        with patch("asistencia.views.timezone.localdate", return_value=date(2026, 5, 30)):
            response = self.client.post(
                "/marcar/entrada/",
                {"latitud": "-12.046374", "longitud": "-77.042793"},
            )
        self.assertEqual(response.status_code, 200)

    def test_entrada_con_gps_valido_registra(self):
        self.client.login(username="practicante1", password="test1234")
        response = self.client.post(
            "/marcar/entrada/",
            {"latitud": "-12.046374", "longitud": "-77.042793", "precisión": "10"},
        )
        self.assertEqual(response.status_code, 200)
        registro = RegistroAsistencia.objects.get(empleado=self.empleado)
        self.assertIsNotNone(registro.hora_entrada)
        self.assertIsNotNone(registro.latitud_entrada)

    def test_salida_para_pphh_no_exige_actividad(self):
        self.empleado.rol = CustomUser.ROL_PPHH
        self.empleado.save(update_fields=["rol"])
        self.client.login(username="practicante1", password="test1234")

        fecha = date(2026, 5, 26)
        RegistroAsistencia.objects.create(
            empleado=self.empleado,
            fecha=fecha,
            hora_entrada=timezone.make_aware(datetime.combine(fecha, time(9, 0))),
            estado=RegistroAsistencia.ESTADO_A_TIEMPO,
        )

        with patch("asistencia.views.timezone.localdate", return_value=fecha), patch(
            "asistencia.views.timezone.now",
            return_value=timezone.make_aware(datetime.combine(fecha, time(18, 0))),
        ):
            response = self.client.post("/marcar/salida/")

        self.assertEqual(response.status_code, 200)
        registro = RegistroAsistencia.objects.get(empleado=self.empleado, fecha=fecha)
        self.assertIsNotNone(registro.hora_salida)
        self.assertIsNone(registro.actividad_diaria)

    def test_dashboard_pphh_no_muestra_actividad_obligatoria(self):
        self.empleado.rol = CustomUser.ROL_PPHH
        self.empleado.save(update_fields=["rol"])
        self.client.login(username="practicante1", password="test1234")

        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Resumen de Actividades del Día")


