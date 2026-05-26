## ADENDA AL PLAN DE DESARROLLO (ESTÁNDARES DE CALIDAD)

FATE 1.5 - CAPA DE PRUEBAS (TESTING):
- Antes de diseñar el frontend, escribir pruebas unitarias ('tests.py') para validar la lógica de IPs, asignación de estados (a_tiempo/tardanza/falta) y solapamiento de fechas de vacaciones.

FASE 4.5 - PROTECCIÓN ANTIFRAUDE:
- El marcado debe procesarse estrictamente con el 'timezone.now()' del servidor Django. Queda prohibido confiar en la hora o fecha enviada por el navegador o dispositivo del usuario.

FASE 7 - DESPLIEGUE Y PRODUCCIÓN:
- Implementar 'django-environ' para la seguridad de credenciales.
- Configurar 'WhiteNoise' para el manejo eficiente de archivos estáticos en producción.
- Generar archivos 'Dockerfile' y 'docker-compose.yml' para asegurar la portabilidad total del sistema (Django + PostgreSQL).