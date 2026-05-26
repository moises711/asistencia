from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Area, AusenciaProgramada, CustomUser, Horario, IpOficinaAutorizada, Justificacion, DiaFeriado, MetaHorasPracticante


class JustificacionForm(forms.ModelForm):
    class Meta:
        model = Justificacion
        fields = ["motivo"]
        widgets = {
            "motivo": forms.Textarea(attrs={"rows": 4}),
        }


class IpOficinaAutorizadaForm(forms.ModelForm):
    class Meta:
        model = IpOficinaAutorizada
        fields = ["nombre_sede", "ip_publica", "activa"]


class AusenciaProgramadaForm(forms.ModelForm):
    class Meta:
        model = AusenciaProgramada
        fields = ["empleado", "fecha_inicio", "fecha_fin", "motivo"]
        widgets = {
            "empleado": forms.Select(),
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
            "motivo": forms.TextInput(attrs={"placeholder": "Motivo de la ausencia"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["empleado"].queryset = CustomUser.objects.filter(
            rol=CustomUser.ROL_EMPLEADO, is_active=True
        ).order_by("last_name", "first_name")
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:border-red-500/60 focus:ring-1 focus:ring-red-500/60 outline-none transition",
            })

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("fecha_inicio")
        fin = cleaned.get("fecha_fin")
        if inicio and fin and fin < inicio:
            raise forms.ValidationError("La fecha fin no puede ser anterior a la fecha inicio.")
        return cleaned


class EmpleadoCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "dni",
            "supervisor",
            "horario",
            "area",
            "rol",
            "permite_remoto",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supervisor"].queryset = CustomUser.objects.filter(
            rol__in=[CustomUser.ROL_ADMIN, CustomUser.ROL_RRHH, CustomUser.ROL_SUPERVISOR],
            is_active=True,
        )
        self.fields["rol"].initial = CustomUser.ROL_EMPLEADO

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = self.cleaned_data.get("rol", CustomUser.ROL_EMPLEADO)
        if commit:
            usuario.save()
            self.save_m2m()
        return usuario

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ["nombre", "descripcion"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = [
            "nombre", 
            "hora_entrada", 
            "hora_salida", 
            "tolerancia_minutos",
            "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"
        ]
        widgets = {
            "hora_entrada": forms.TimeInput(attrs={"type": "time"}),
            "hora_salida": forms.TimeInput(attrs={"type": "time"}),
        }


class DiaFeriadoForm(forms.ModelForm):
    class Meta:
        model = DiaFeriado
        fields = ["fecha", "descripcion"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
        }


class MetaHorasPracticanteForm(forms.ModelForm):
    class Meta:
        model = MetaHorasPracticante
        fields = ["empleado", "horas_totales_requeridas", "fecha_inicio_practica", "fecha_fin_practica"]
        widgets = {
            "fecha_inicio_practica": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin_practica": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["empleado"].queryset = CustomUser.objects.filter(
            rol=CustomUser.ROL_EMPLEADO, is_active=True
        ).order_by("last_name", "first_name")
