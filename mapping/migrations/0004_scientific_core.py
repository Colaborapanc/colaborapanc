from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0003_mensagem_fields_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='pontopanc',
            name='atualizado_em',
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='status_fluxo',
            field=models.CharField(choices=[('rascunho', 'Rascunho'), ('submetido', 'Submetido'), ('em_revisao', 'Em revisão'), ('validado', 'Validado'), ('rejeitado', 'Rejeitado'), ('necessita_revisao', 'Necessita revisão')], default='rascunho', max_length=20, verbose_name='Status do fluxo científico'),
        ),
        migrations.AddIndex(
            model_name='pontopanc',
            index=models.Index(fields=['status_fluxo', 'status_validacao'], name='mapping_pon_status__4eb38f_idx'),
        ),
        migrations.CreateModel(
            name='APIUsageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_name', models.CharField(max_length=40)),
                ('month', models.CharField(max_length=7)),
                ('limit', models.PositiveIntegerField(default=0)),
                ('used', models.PositiveIntegerField(default=0)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-month', 'api_name'],
                'unique_together': {('api_name', 'month')},
            },
        ),
        migrations.CreateModel(
            name='HistoricoValidacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evento', models.CharField(max_length=80)),
                ('dados', models.JSONField(blank=True, default=dict)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('ponto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historico_validacoes', to='mapping.pontopanc')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='HistoricoIdentificacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metodo', models.CharField(choices=[('google_vision', 'Google Cloud Vision'), ('plantnet', 'PlantNet'), ('plantid', 'Plant.id'), ('custom_ml', 'Base Customizada (ML)'), ('manual', 'Identificação Manual')], max_length=30, verbose_name='Método de identificação')),
                ('imagem', models.ImageField(blank=True, null=True, upload_to='identificacoes/', verbose_name='Imagem analisada')),
                ('score_confianca', models.FloatField(help_text='De 0 a 100', verbose_name='Score de confiança')),
                ('resultados_completos', models.JSONField(blank=True, help_text='JSON com todos os resultados da API', null=True, verbose_name='Resultados completos')),
                ('sucesso', models.BooleanField(default=True, verbose_name='Identificação bem-sucedida')),
                ('erro', models.TextField(blank=True, verbose_name='Mensagem de erro')),
                ('tempo_processamento', models.FloatField(blank=True, null=True, verbose_name='Tempo de processamento (segundos)')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('planta_identificada', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='identificacoes', to='mapping.plantareferencial')),
                ('ponto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='historico_identificacoes', to='mapping.pontopanc')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Histórico de Identificação',
                'verbose_name_plural': 'Históricos de Identificação',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='PredicaoIA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provedor', models.CharField(max_length=30)),
                ('predicoes_top_k', models.JSONField(default=list)),
                ('score_confianca', models.FloatField(help_text='Score de 0 a 1')),
                ('faixa_risco', models.CharField(choices=[('alto', 'Alta confiança'), ('medio', 'Média confiança'), ('baixo', 'Baixa confiança')], max_length=10)),
                ('justificativa', models.TextField(blank=True)),
                ('requer_revisao_humana', models.BooleanField(default=True)),
                ('fonte_predicao', models.CharField(blank=True, max_length=80)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('historico_identificacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='predicoes_estruturadas', to='mapping.historicoidentificacao')),
                ('ponto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predicoes_ia', to='mapping.pontopanc')),
            ],
            options={
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='ValidacaoEspecialista',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decisao_final', models.CharField(choices=[('validado', 'Validado'), ('rejeitado', 'Rejeitado'), ('necessita_revisao', 'Necessita revisão')], max_length=20)),
                ('especie_final', models.CharField(blank=True, max_length=200)),
                ('motivo_divergencia', models.TextField(blank=True)),
                ('observacao', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('ponto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='validacoes_especialistas', to='mapping.pontopanc')),
                ('predicao_ia', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='validacoes', to='mapping.predicaoia')),
                ('revisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='validacoes_realizadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-criado_em'],
            },
        ),
        migrations.AddIndex(
            model_name='historicoidentificacao',
            index=models.Index(fields=['usuario', 'metodo'], name='mapping_his_usuario_76b8ee_idx'),
        ),
        migrations.AddIndex(
            model_name='historicoidentificacao',
            index=models.Index(fields=['sucesso', 'metodo'], name='mapping_his_sucesso_0dcb71_idx'),
        ),
        migrations.AddIndex(
            model_name='historicovalidacao',
            index=models.Index(fields=['ponto', 'evento', 'criado_em'], name='mapping_his_ponto_i_2d8655_idx'),
        ),
        migrations.AddIndex(
            model_name='predicaoia',
            index=models.Index(fields=['ponto', 'provedor', 'criado_em'], name='mapping_pre_ponto_i_e82a23_idx'),
        ),
        migrations.AddIndex(
            model_name='validacaoespecialista',
            index=models.Index(fields=['ponto', 'decisao_final', 'criado_em'], name='mapping_val_ponto_i_a90f73_idx'),
        ),
    ]
