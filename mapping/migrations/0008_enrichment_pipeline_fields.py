from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mapping", "0007_enriquecimento_taxonomico"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pontopanc",
            name="status_enriquecimento",
            field=models.CharField(
                choices=[
                    ("pendente", "Pendente"),
                    ("parcial", "Parcialmente validado"),
                    ("completo", "Completo"),
                    ("falho", "Falho"),
                ],
                default="pendente",
                max_length=20,
                verbose_name="Status do enriquecimento",
            ),
        ),
        migrations.AlterField(
            model_name="pontopanc",
            name="fontes_secundarias",
            field=models.JSONField(blank=True, default=list, verbose_name="Fontes secundárias (legado)"),
        ),
        migrations.AlterField(
            model_name="pontopanc",
            name="grau_confianca",
            field=models.FloatField(default=0.0, verbose_name="Grau de confiança (legado)"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="fontes_taxonomicas_secundarias",
            field=models.JSONField(blank=True, default=list, verbose_name="Fontes taxonômicas secundárias"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="grau_confianca_taxonomica",
            field=models.FloatField(default=0.0, verbose_name="Grau de confiança taxonômica"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="payload_resumido_validacao",
            field=models.JSONField(blank=True, default=dict, verbose_name="Payload resumido de validação"),
        ),
        migrations.AddField(
            model_name="pontopanc",
            name="validacao_pendente_revisao_humana",
            field=models.BooleanField(default=False, verbose_name="Validação pendente de revisão humana"),
        ),
        migrations.AlterField(
            model_name="enriquecimentotaxonomicohistorico",
            name="status",
            field=models.CharField(
                choices=[
                    ("pendente", "Pendente"),
                    ("parcial", "Parcialmente validado"),
                    ("completo", "Completo"),
                    ("falho", "Falho"),
                ],
                default="pendente",
                max_length=20,
            ),
        ),
    ]
