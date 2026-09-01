from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('asistencia', '0010_registroasistencia_tipo_entrada_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DispositivoToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=64, unique=True)),
                ('nombre_dispositivo', models.CharField(blank=True, max_length=120)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('ultimo_uso', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tokens_dispositivo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Token de dispositivo',
                'verbose_name_plural': 'Tokens de dispositivo',
            },
        ),
    ]
