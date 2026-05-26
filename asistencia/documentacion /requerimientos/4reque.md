1. Paleta de Colores y Estilo General (Tailwind)

    Fondo General: Gris ultra claro (bg-gray-50) para dar sensación de limpieza.

    Color Primario (Corporativo): Azul Índigo (bg-indigo-600 / text-indigo-600) para botones principales, enlaces y bordes activos.

    Estados Dinámicos:

        Verde (emerald-500): Para el estado "A tiempo", botones de éxito y red Wi-Fi verificada.

        Amarillo (amber-500): Para el estado "Tardanza" y alertas de almuerzo.

        Rojo (rose-500): Para el estado "Falta", solicitudes rechazadas o alertas de red bloqueada.

2. Estructura Visual de las Vistas (Mockups en Texto)
Vista A: Pantalla de Login (/login/)

Una tarjeta centralizada, limpia y minimalista, optimizada para pantallas móviles.

    Componentes:

        Logo de la empresa o icono de reloj en la parte superior.

        Input de DNI / Usuario (con bordes redondeados rounded-lg).

        Input de Contraseña.

        Botón grande de "Iniciar Sesión" (bg-indigo-600 text-white w-full py-3).

Vista B: El Dashboard del Empleado (/dashboard/) — La más importante

Debe estar diseñada en bloques verticales (tarjetas) para que en un celular todo quede al alcance del pulgar.
Plaintext

+-----------------------------------------------------+
| [Icono Usuario] Hola, Carlos Torres    (Cerrar Sesión)|
+-----------------------------------------------------+
| TARJETA 1: RELOJ Y ESTADO DE RED                    |
|   12:15:43 PM  -- Lunes, 25 de Mayo                 |
|   [Icono Wifi Verde] Conectado a: Red Oficina Central|
+-----------------------------------------------------+
| TARJETA 2: BOTONES DE ACCIÓN (Reactivos)            |
|                                                     |
|   [ BOTÓN: INICIAR ALMUERZO ] (Activo en este color)|
|   (El botón de "Entrada" ya se pone gris y oculto)  |
+-----------------------------------------------------+
| TARJETA 3: RESUMEN DEL DÍA                          |
|   Entrada: 08:55 AM | Estado: A Tiempo             |
+-----------------------------------------------------+
| TARJETA 4: ÚLTIMOS 5 REGISTROS (Historial rápido)   |
|   - Viernes 22/05: 09:02 AM [Tardanza]              |
|   - Jueves 21/05:  08:45 AM [A Tiempo]             |
+-----------------------------------------------------+

Vista C: Panel de Control del Administrador (/panel-control/)

Una estructura de tipo Dashboard administrativo (Sidebar a la izquierda en pantallas grandes, menú hamburguesa en móviles).

    Fila de Kpis (Tarjetas de métricas rápidas en la parte superior):

        Tarjeta 1: Total de Empleados Hoy (Número grande).

        Tarjeta 2: Presentes (Verde).

        Tarjeta 3: Tardanzas (Amarillo).

        Tarjeta 4: Faltas (Rojo).

    Cuerpo Principal:

        Tabla interactiva de asistencias del día con avatares redondos para los empleados, badges de colores para los estados (span con clases de Tailwind como px-2 py-1 rounded-full text-xs font-semibold), e IPs de registro visibles.