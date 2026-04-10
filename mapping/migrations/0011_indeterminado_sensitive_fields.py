from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0010_enrichment_structured_fields_and_integration_monitor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pontopanc',
            name='comestibilidade_status',
            field=models.CharField(default='indeterminado', max_length=20, verbose_name='Comestibilidade (status)'),
        ),
        migrations.AlterField(
            model_name='pontopanc',
            name='parte_comestivel_lista',
            field=models.JSONField(blank=True, default=None, null=True, verbose_name='Partes comestíveis normalizadas'),
        ),
        migrations.AlterField(
            model_name='pontopanc',
            name='frutificacao_meses',
            field=models.JSONField(blank=True, default=None, null=True, verbose_name='Meses de frutificação normalizados'),
        ),
        migrations.AlterField(
            model_name='pontopanc',
            name='colheita_periodo',
            field=models.JSONField(blank=True, default=None, null=True, verbose_name='Período de colheita consolidado'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='comestibilidade_confirmada',
            field=models.BooleanField(default=False, verbose_name='Comestibilidade confirmada'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='parte_comestivel_confirmada',
            field=models.BooleanField(default=False, verbose_name='Parte comestível confirmada'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='frutificacao_confirmada',
            field=models.BooleanField(default=False, verbose_name='Frutificação confirmada'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='colheita_confirmada',
            field=models.BooleanField(default=False, verbose_name='Colheita confirmada'),
        ),
        migrations.AddField(
            model_name='pontopanc',
            name='fontes_campos_enriquecimento',
            field=models.JSONField(blank=True, default=dict, verbose_name='Fontes por campo enriquecido'),
        ),
    ]
