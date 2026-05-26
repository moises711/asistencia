🔒 Módulo de Validación por Red Local (Wi-Fi / IP Pública)

Para asegurar que los empleados solo marquen dentro de la oficina, implementaremos una validación por IP Pública Externa o por Subred Local. La forma más segura y fácil de implementar en Django (sin instalar apps en los teléfonos) es validar la IP pública desde la que se reciben las peticiones HTTP.
1. Nuevos Requerimientos (PRD)

    RF6: Restricción por IP de Oficina: El sistema solo permitirá el marcado de entrada/salida si la petición proviene de la IP pública de la oficina o de una lista de IPs autorizadas.

    RF7: Modo Home Office / Excepciones: El Administrador puede activar un check en el perfil del usuario llamado permite_remoto. Si está activo, el sistema se salta la validación de la IP de la oficina.

2. Modificaciones en la Base de Datos (Modelos)

Necesitamos una tabla para guardar las IPs autorizadas de la oficina (por si tienen más de una conexión a internet o cambia en el futuro) y un campo en el usuario.

    En el modelo CustomUser (Añadir campo):

        permite_remoto (BooleanField, default=False)

    Nuevo Modelo IpOficinaAutorizada:

        nombre_sede (CharField, ej: "Oficina Central")

        ip_publica (GenericIPAddressField)

        activa (BooleanField, default=True)

3. Proceso y Lógica de Negocio (El Flujo para la IA)

Cuando el empleado presione el botón "Registrar Entrada", la IA debe ejecutar este flujo en la vista de Django:

    Obtener la IP real del cliente: Django suele recibir la IP en request.META['REMOTE_ADDR']. (Nota: Si usas un proxy como Nginx, debe buscar en HTTP_X_FORWARDED_FOR).

    Verificar Excepción: ¿El usuario tiene permite_remoto == True?

        Sí: Saltar validación de IP y registrar asistencia.

        No: Continuar al paso 3.

    Validar IP: ¿La IP del cliente coincide con alguna de las IPs registradas en IpOficinaAutorizada?

        Sí: Permitir el marcado con éxito.

        No: Bloquear la acción, no registrar nada y devolver un mensaje de error: "No estás conectado a la red Wi-Fi de la oficina. Registro no permitido".

4. Fragmento de Lógica para tu IA (Mixins/Middleware)

Dile a tu IA que diseñe una función utilitaria o un Mixin para las vistas. Este es el algoritmo que la IA debe escribir en Python:
Python

def obtener_ip_cliente(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Lógica dentro de la vista de marcado:
ip_empleado = obtener_ip_cliente(request)

if not request.user.permite_remoto:
    ip_valida = IpOficinaAutorizada.objects.filter(ip_publica=ip_empleado, activa=True).exists()
    if not ip_valida:
        return JsonResponse({
            "status": "error", 
            "message": f"Acceso denegado. Tu IP actual ({ip_empleado}) no pertenece a la red de la oficina."
        }, status=403)

5. Nuevas Vistas y Elementos de Interfaz (Vistas/Templates)

    Vista de Configuración (Admin): Un pequeño formulario donde el administrador pueda entrar, ver cuál es la IP actual de la oficina (el sistema se la puede auto-detectar en pantalla para facilitarle la vida) y guardarla con el botón "Autorizar esta Red".

    Componente Visual en el Dashboard: * Si el empleado está en la IP correcta, el botón de marcado se muestra Verde e interactivo.

        Si está en otra red (y no es remoto), el botón se muestra Gris/Bloqueado con un candado que dice: "Conéctate al Wi-Fi de la empresa para marcar".

⚠️ Un detalle técnico muy importante que debes saber:

Las redes de internet de las oficinas a veces tienen IPs Dinámicas (cambian cada vez que se apaga o reinicia el router).

    Si tu internet es de IP Fija (Estática), esto funcionará perfecto para siempre.

    Si tu internet tiene IP Dinámica, dile a la IA: "Agrega una opción para que el Supervisor pueda actualizar la IP autorizada de la oficina de forma rápida con un solo clic desde su teléfono cuando cambie".

## REQUERIMIENTOS ADICIONALES DE NEGOCIO (LOGICA AVANZADA)

1. MODELO HORARIOS: Crear tabla 'Horario' (hora_entrada, hora_salida, tolerancia_minutos). Vincular a CustomUser.
2. CONTROL DE BREAKS: Añadir soporte en 'RegistroAsistencia' para registrar la hora de salida y entrada de almuerzo. Los botones del Dashboard deben actualizarse en consecuencia.
3. LOG DE AUDITORÍA: Si un Administrador edita manualmente un registro de asistencia en el backend o frontend, registrar obligatoriamente 'modificado_por', 'fecha_modificacion' y un texto de 'motivo_modificacion'.
4. ALERTAS: Implementar señales (signals) para enviar correos de notificación cuando un empleado registre una "Tardanza" o cuando un Supervisor reciba una nueva "Solicitud de Justificación".