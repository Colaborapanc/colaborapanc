import django.db.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mapping', '0007_merge_20260403_0001'),
    ]

    operations = [
        # ---- Campos de enriquecimento em PlantaReferencial ----
        migrations.AddField(
            model_name='plantareferencial',
            name='nome_cientifico_submetido',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='Nome científico submetido'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='nome_cientifico_validado',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='Nome científico validado (Global Names)'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='nome_aceito',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='Nome aceito (Tropicos)'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='sinonimos',
            field=models.JSONField(blank=True, default=list, verbose_name='Sinônimos'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='autoria',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='Autoria'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='fonte_taxonomica_primaria',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Fonte taxonômica primária'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='fontes_secundarias',
            field=models.JSONField(blank=True, default=list, verbose_name='Fontes secundárias'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='grau_confianca',
            field=models.FloatField(blank=True, help_text='0.0 a 1.0', null=True, verbose_name='Grau de confiança do enriquecimento'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='distribuicao_resumida',
            field=models.TextField(blank=True, null=True, verbose_name='Distribuição resumida'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='ocorrencias_gbif',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Ocorrências GBIF'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='ocorrencias_inaturalist',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Ocorrências iNaturalist'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='fenologia_observada',
            field=models.JSONField(blank=True, default=dict, verbose_name='Fenologia observada (iNaturalist)'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='imagem_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='URL da imagem de referência'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='imagem_fonte',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Fonte da imagem'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='licenca_imagem',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Licença da imagem'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='ultima_validacao_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Última validação taxonômica'),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='status_enriquecimento',
            field=models.CharField(
                choices=[('pendente', 'Pendente'), ('completo', 'Completo'), ('parcial', 'Parcial'), ('erro', 'Erro')],
                default='pendente', max_length=30, verbose_name='Status do enriquecimento',
            ),
        ),
        migrations.AddField(
            model_name='plantareferencial',
            name='payload_enriquecimento',
            field=models.JSONField(blank=True, default=dict, verbose_name='Payload resumido do enriquecimento'),
        ),

        # ---- Modelo HistoricoEnriquecimento ----
        migrations.CreateModel(
            name='HistoricoEnriquecimento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateTimeField(auto_now_add=True, verbose_name='Data do enriquecimento')),
                ('fontes_consultadas', models.JSONField(default=list, verbose_name='Fontes consultadas')),
                ('resultado', models.JSONField(default=dict, verbose_name='Resultado completo')),
                ('status', models.CharField(
                    choices=[('completo', 'Completo'), ('parcial', 'Parcial'), ('erro', 'Erro')],
                    default='parcial', max_length=30, verbose_name='Status',
                )),
                ('erro_detalhes', models.TextField(blank=True, null=True, verbose_name='Detalhes de erros')),
                ('planta', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historico_enriquecimento',
                    to='mapping.plantareferencial',
                )),
                ('usuario', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='enriquecimentos_realizados',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Histórico de enriquecimento',
                'verbose_name_plural': 'Históricos de enriquecimento',
                'ordering': ['-data'],
            },
        ),
    ]
