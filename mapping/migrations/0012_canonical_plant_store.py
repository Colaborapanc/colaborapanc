from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("mapping", "0011_indeterminado_sensitive_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="plantareferencial",
            name="aliases",
            field=models.JSONField(blank=True, default=list, verbose_name="Aliases consolidados"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="descricao_consolidada",
            field=models.TextField(blank=True, default="", verbose_name="Descrição consolidada"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="descricao_resumida",
            field=models.TextField(blank=True, default="", verbose_name="Descrição resumida"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="enriquecimento_completo_em",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Enriquecimento completo em"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="especie",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="Epíteto específico"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="familia",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="Família botânica"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="fontes_utilizadas",
            field=models.JSONField(blank=True, default=list, verbose_name="Fontes utilizadas para ficha canônica"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="genero",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="Gênero botânico"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="is_fully_enriched",
            field=models.BooleanField(default=False, verbose_name="Ficha canônica totalmente enriquecida"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="nivel_confianca_enriquecimento",
            field=models.FloatField(default=0.0, verbose_name="Nível de confiança consolidado"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="nomes_populares",
            field=models.JSONField(blank=True, default=list, verbose_name="Nomes populares consolidados"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="sazonalidade",
            field=models.JSONField(blank=True, default=dict, verbose_name="Sazonalidade estruturada"),
        ),
        migrations.AddField(
            model_name="plantareferencial",
            name="toxicidade",
            field=models.CharField(blank=True, default="", max_length=200, verbose_name="Toxicidade"),
        ),
        migrations.CreateModel(
            name="PlantaAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Alias")),
                ("normalized_name", models.CharField(db_index=True, max_length=255, verbose_name="Alias normalizado")),
                ("source", models.CharField(blank=True, default="", max_length=100, verbose_name="Origem do alias")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "planta",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="aliases_registrados", to="mapping.plantareferencial"),
                ),
            ],
            options={"ordering": ["name"], "unique_together": {("planta", "normalized_name")}},
        ),
    ]
