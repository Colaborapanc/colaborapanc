from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("mapping", "0006_eventomonitorado"),
    ]

    operations = [
        migrations.AddField(
            model_name="pontopanc",
            name="autoria",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="Autoria"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="distribuicao_resumida",
            field=models.TextField(blank=True, null=True, verbose_name="Distribuição resumida"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="enriquecimento_atualizado_em",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Enriquecimento atualizado em"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="fenologia_observada",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Fenologia observada"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="fonte_taxonomica_primaria",
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name="Fonte taxonômica primária"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="fontes_enriquecimento",
            field=models.JSONField(blank=True, default=list, verbose_name="Fontes do enriquecimento"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="fontes_secundarias",
            field=models.JSONField(blank=True, default=list, verbose_name="Fontes secundárias"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="grau_confianca",
            field=models.FloatField(default=0.0, verbose_name="Grau de confiança"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="imagem_fonte",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Fonte da imagem"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="imagem_url",
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name="Imagem URL"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="licenca_imagem",
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name="Licença da imagem"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="nome_aceito",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="Nome aceito"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="nome_cientifico_submetido",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="Nome científico submetido"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="nome_cientifico_validado",
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name="Nome científico validado"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="ocorrencias_gbif",
            field=models.IntegerField(default=0, verbose_name="Ocorrências GBIF"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="ocorrencias_inaturalist",
            field=models.IntegerField(default=0, verbose_name="Ocorrências iNaturalist"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="payload_enriquecimento",
            field=models.JSONField(blank=True, default=dict, verbose_name="Payload resumido de enriquecimento"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="sinonimos",
            field=models.JSONField(blank=True, default=list, verbose_name="Sinônimos"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="status_enriquecimento",
            field=models.CharField(
                choices=[("pendente", "Pendente"), ("parcial", "Parcialmente validado"), ("validado", "Validado")],
                default="pendente",
                max_length=20,
                verbose_name="Status do enriquecimento",
            ),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="ultima_validacao_em",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Última validação em"),
        ),
        migrations.CreateModel(
            name="EnriquecimentoTaxonomicoHistorico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pendente", "Pendente"), ("parcial", "Parcialmente validado"), ("validado", "Validado")], default="pendente", max_length=20)),
                ("grau_confianca", models.FloatField(default=0.0)),
                ("fontes", models.JSONField(blank=True, default=list)),
                ("payload_resumido", models.JSONField(blank=True, default=dict)),
                ("executado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "ponto",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="historico_enriquecimento", to="mapping.pontopanc"),
                ),
            ],
            options={"ordering": ["-executado_em"]},
        ),
    ]
