from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models as django_models

from .models import (
    AusenciaProgramada,
    CustomUser,
    DiaFeriado,
    Horario,
    IpOficinaAutorizada,
    Justificacion,
    RegistroAsistencia,
    Area,
    ConfiguracionGPS,
    DispositivoToken,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Datos de asistencia",
            {
                "fields": (
                    "rol",
                    "dni",
                    "supervisor",
                    "horario",
                    "area",
                    "permite_remoto",
                )
            },
        ),
    )
    list_display = ("username", "email", "rol", "dni", "is_active")
    list_filter = ("rol", "is_active")
    search_fields = ("username", "email", "dni")


admin.site.register(Horario)
admin.site.register(IpOficinaAutorizada)
admin.site.register(RegistroAsistencia)
admin.site.register(Justificacion)
admin.site.register(AusenciaProgramada)
admin.site.register(DiaFeriado)
admin.site.register(Area)


@admin.register(ConfiguracionGPS)
class ConfiguracionGPSAdmin(admin.ModelAdmin):
    """Admin para configuración de ubicación GPS"""
    readonly_fields = ('creada_en', 'actualizada_en', 'capturar_gps_button', 'ubicacion_actual')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'activa')
        }),
        ('Ubicación GPS', {
            'fields': ('latitud', 'longitud'),
            'description': 'Coordenadas de la oficina principal'
        }),
        ('Radio de Validación', {
            'fields': ('radio_permitido_metros',),
            'description': 'Radio en metros permitido para marcar asistencia'
        }),
        ('Herramientas', {
            'fields': ('capturar_gps_button', 'ubicacion_actual'),
            'description': 'Usa el botón para capturar tu ubicación actual'
        }),
        ('Metadata', {
            'fields': ('creada_en', 'actualizada_en'),
            'classes': ('collapse',)
        }),
    )
    
    list_display = ('nombre', 'latitud_display', 'longitud_display', 'radio_display', 'activa_display')
    list_filter = ('activa', 'creada_en')
    search_fields = ('nombre',)
    
    def latitud_display(self, obj):
        return f"{obj.latitud}" if obj.latitud else "-"
    latitud_display.short_description = "Latitud"
    
    def longitud_display(self, obj):
        return f"{obj.longitud}" if obj.longitud else "-"
    longitud_display.short_description = "Longitud"
    
    def radio_display(self, obj):
        return f"{obj.radio_permitido_metros}m"
    radio_display.short_description = "Radio"
    
    def activa_display(self, obj):
        color = 'green' if obj.activa else 'red'
        estado = '✓ Activa' if obj.activa else '✗ Inactiva'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            estado
        )
    activa_display.short_description = "Estado"
    
    def capturar_gps_button(self, obj):
        """Botón para capturar GPS desde el navegador"""
        html = '''
        <button id="btn-capturar-gps" type="button" 
                style="padding: 10px 20px; background-color: #417690; color: white; 
                       border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">
            📍 Capturar Ubicación Actual
        </button>
        <div id="gps-status" style="margin-top: 10px; padding: 10px; border-radius: 5px; 
                                    background-color: #f0f0f0; display: none;">
            <p id="gps-mensaje" style="margin: 0; color: #333;"></p>
        </div>
        
        <script>
        document.getElementById('btn-capturar-gps').addEventListener('click', function() {
            const btn = this;
            const statusDiv = document.getElementById('gps-status');
            const mensaje = document.getElementById('gps-mensaje');
            
            btn.disabled = true;
            btn.textContent = '⏳ Obteniendo ubicación...';
            btn.style.opacity = '0.6';
            statusDiv.style.display = 'block';
            statusDiv.style.backgroundColor = '#fff3cd';
            mensaje.style.color = '#856404';
            mensaje.textContent = 'Obteniendo coordenadas GPS...';
            
            if (!navigator.geolocation) {
                statusDiv.style.backgroundColor = '#f8d7da';
                mensaje.style.color = '#721c24';
                mensaje.innerHTML = '❌ Error: Geolocalización no soportada en este navegador';
                btn.disabled = false;
                btn.textContent = '📍 Capturar Ubicación Actual';
                btn.style.opacity = '1';
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    const precision = position.coords.accuracy;
                    
                    // Llenar los campos
                    document.querySelector('input[name="latitud"]').value = lat;
                    document.querySelector('input[name="longitud"]').value = lon;
                    
                    statusDiv.style.backgroundColor = '#d4edda';
                    mensaje.style.color = '#155724';
                    mensaje.innerHTML = `✅ Ubicación capturada exitosamente!<br>
                                        📍 Latitud: ${lat.toFixed(6)}<br>
                                        📍 Longitud: ${lon.toFixed(6)}<br>
                                        📏 Precisión: ${precision.toFixed(1)}m`;
                    
                    btn.textContent = '✅ Ubicación Capturada';
                    btn.style.backgroundColor = '#28a745';
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = '📍 Capturar Ubicación Actual';
                        btn.style.opacity = '1';
                    }, 3000);
                },
                function(error) {
                    let errorMsg = 'Error desconocido';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMsg = '❌ Permiso denegado. Habilita GPS en tu navegador.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMsg = '❌ Información de GPS no disponible.';
                            break;
                        case error.TIMEOUT:
                            errorMsg = '❌ Tiempo de espera agotado. Intenta de nuevo.';
                            break;
                    }
                    
                    statusDiv.style.backgroundColor = '#f8d7da';
                    mensaje.style.color = '#721c24';
                    mensaje.textContent = errorMsg;
                    
                    btn.disabled = false;
                    btn.textContent = '📍 Capturar Ubicación Actual';
                    btn.style.opacity = '1';
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
        </script>
        '''
        return format_html(html)
    capturar_gps_button.short_description = "Capturar GPS"
    
    def ubicacion_actual(self, obj):
        """Muestra la ubicación guardada actual"""
        if obj.latitud and obj.longitud:
            mapa_url = f"https://www.google.com/maps/?q={obj.latitud},{obj.longitud}"
            return format_html(
                '<a href="{}" target="_blank" style="color: #417690; text-decoration: none;">'
                '📍 Ver en Google Maps<br>'
                'Lat: {:.6f}<br>Lon: {:.6f}</a>',
                mapa_url,
                float(obj.latitud),
                float(obj.longitud)
            )
        return "No configurada"
    ubicacion_actual.short_description = "Ubicación Actual"
    
    def has_add_permission(self, request):
        """Permitir agregar solo si no existe una configuración activa"""
        return ConfiguracionGPS.objects.filter(activa=True).count() == 0 or request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """Al guardar, desactivar otras configuraciones si esta es activa"""
        if obj.activa:
            ConfiguracionGPS.objects.filter(activa=True).exclude(pk=obj.pk).update(activa=False)
        super().save_model(request, obj, form, change)


admin.site.register(DispositivoToken)
