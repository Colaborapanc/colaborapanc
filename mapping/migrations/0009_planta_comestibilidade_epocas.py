from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mapping", "0008_enrichment_pipeline_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="plantareferencial",
            name="comestivel",
            field=models.BooleanField(blank=True, default=None, null=True, verbose_name="Comestível"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="epoca_colheita",
            field=models.CharField(blank=True, default="Não informado", max_length=120, verbose_name="Colheita (período do ano)"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="epoca_frutificacao",
            field=models.CharField(blank=True, default="Não informado", max_length=120, verbose_name="Frutificação (meses)"),
        ),
    ]
