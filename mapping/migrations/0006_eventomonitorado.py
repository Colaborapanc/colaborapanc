from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0005_ensure_default_site'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventoMonitorado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fonte', models.CharField(choices=[('mapbiomas', 'MapBiomas Alerta'), ('nasa_firms', 'NASA FIRMS'), ('climatico', 'Alerta Climático')], max_length=30)),
                ('tipo_evento', models.CharField(choices=[('desmatamento', 'Desmatamento'), ('foco_calor', 'Foco de Calor'), ('incendio', 'Incêndio'), ('climatico', 'Climático')], max_length=30)),
                ('external_id', models.CharField(blank=True, max_length=120, null=True)),
                ('hash_evento', models.CharField(blank=True, max_length=120, null=True)),
                ('titulo', models.CharField(blank=True, default='', max_length=255)),
                ('descricao', models.TextField(blank=True, default='')),
                ('ocorrido_em', models.DateTimeField()),
                ('publicado_em', models.DateTimeField(blank=True, null=True)),
                ('latitude_evento', models.FloatField(blank=True, null=True)),
                ('longitude_evento', models.FloatField(blank=True, null=True)),
                ('bbox', models.JSONField(blank=True, null=True)),
                ('area_afetada_ha', models.FloatField(blank=True, null=True)),
                ('distancia_metros', models.FloatField(blank=True, null=True)),
                ('severidade', models.CharField(blank=True, default='', max_length=50)),
                ('confianca', models.CharField(blank=True, default='', max_length=50)),
                ('brilho', models.FloatField(blank=True, null=True)),
                ('frp', models.FloatField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('status_sync', models.CharField(choices=[('novo', 'Novo'), ('atualizado', 'Atualizado'), ('sincronizado', 'Sincronizado'), ('erro', 'Erro')], default='sincronizado', max_length=20)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('ponto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eventos_monitorados', to='mapping.pontopanc')),
            ],
            options={
                'verbose_name': 'Evento Monitorado',
                'verbose_name_plural': 'Eventos Monitorados',
                'ordering': ['-ocorrido_em'],
                'unique_together': {('ponto', 'fonte', 'external_id', 'ocorrido_em')},
            },
        ),
        migrations.AddIndex(
            model_name='eventomonitorado',
            index=models.Index(fields=['ponto', 'fonte', 'tipo_evento'], name='mapping_eve_ponto_i_8c0fec_idx'),
        ),
        migrations.AddIndex(
            model_name='eventomonitorado',
            index=models.Index(fields=['ocorrido_em'], name='mapping_eve_ocorrid_7ce82e_idx'),
        ),
        migrations.AddIndex(
            model_name='eventomonitorado',
            index=models.Index(fields=['external_id'], name='mapping_eve_externa_d7f0d6_idx'),
        ),
    ]
