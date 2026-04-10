from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0009_planta_comestibilidade_epocas'),
    ]

    operations = [
        migrations.AddField(
            model_name='pontopanc',
            name='colheita_periodo',
            field=models.JSONField(blank=True, default='nao_informado', verbose_name='Período de colheita consolidado'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='comestibilidade_status',
            field=models.CharField(default='nao_informado', max_length=20, verbose_name='Comestibilidade (status)'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='frutificacao_meses',
            field=models.JSONField(blank=True, default=list, verbose_name='Meses de frutificação normalizados'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='integracoes_com_falha',
            field=models.JSONField(blank=True, default=list, verbose_name='Integrações com falha'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='integracoes_utilizadas',
            field=models.JSONField(blank=True, default=list, verbose_name='Integrações utilizadas'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='parte_comestivel_lista',
            field=models.JSONField(blank=True, default=list, verbose_name='Partes comestíveis normalizadas'),
        ),
        migrations.CreateModel(
            name='IntegracaoMonitoramento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=120, unique=True)),
                ('status', models.CharField(choices=[('online', 'Online'), ('degradada', 'Degradada'), ('offline', 'Offline')], default='offline', max_length=20)),
                ('ultimo_teste_bem_sucedido', models.DateTimeField(blank=True, null=True)),
                ('ultimo_erro', models.TextField(blank=True, null=True)),
                ('tempo_resposta_ms', models.IntegerField(blank=True, null=True)),
                ('requer_chave', models.BooleanField(default=False)),
                ('quota_limite', models.CharField(blank=True, max_length=120, null=True)),
                ('endpoint_healthcheck', models.URLField(blank=True, max_length=500, null=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Monitoramento de integração',
                'verbose_name_plural': 'Monitoramento de integrações',
            },
        ),
        migrations.CreateModel(
            name='IntegracaoMonitoramentoLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('detalhe', models.TextField(blank=True, null=True)),
                ('tempo_resposta_ms', models.IntegerField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('integracao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='mapping.integracaomonitoramento')),
            ],
            options={
                'verbose_name': 'Log de integração',
                'verbose_name_plural': 'Logs de integrações',
                'ordering': ['-criado_em'],
            },
        ),
    ]
