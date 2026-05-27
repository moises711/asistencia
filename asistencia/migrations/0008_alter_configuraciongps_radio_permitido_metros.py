from django.db import migrations, models


def actualizar_radio_existente(apps, schema_editor):
    ConfiguracionGPS = apps.get_model("asistencia", "ConfiguracionGPS")
    ConfiguracionGPS.objects.filter(radio_permitido_metros=20).update(radio_permitido_metros=50)


def revertir_radio_existente(apps, schema_editor):
    ConfiguracionGPS = apps.get_model("asistencia", "ConfiguracionGPS")
    ConfiguracionGPS.objects.filter(radio_permitido_metros=50).update(radio_permitido_metros=20)


class Migration(migrations.Migration):

    dependencies = [
        ("asistencia", "0007_alter_customuser_rol"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuraciongps",
            name="radio_permitido_metros",
            field=models.IntegerField(default=50, help_text="Radio permitido en metros para marcar asistencia"),
        ),
        migrations.RunPython(actualizar_radio_existente, revertir_radio_existente),
    ]