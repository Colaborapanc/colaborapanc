from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mapping", "0002_notifications_and_roadmap"),
    ]

    operations = [
        migrations.RenameField(
            model_name="mensagem",
            old_name="texto",
            new_name="conteudo",
        ),
        migrations.RenameField(
            model_name="mensagem",
            old_name="criada_em",
            new_name="enviada_em",
        ),
        migrations.AddField(
            model_name="mensagem",
            name="lida",
            field=models.BooleanField(default=False, verbose_name="Lida"),
        ),
        migrations.AddField(
            model_name="mensagem",
            name="imagem",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="mensagens/",
                verbose_name="Imagem",
            ),
        ),
        migrations.AlterField(
            model_name="mensagem",
            name="conteudo",
            field=models.TextField(blank=True, default="", verbose_name="Conteúdo"),
        ),
        migrations.AlterField(
            model_name="mensagem",
            name="lida_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="mensagem",
            name="enviada_em",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterModelOptions(
            name="mensagem",
            options={"ordering": ["enviada_em"], "verbose_name": "Mensagem", "verbose_name_plural": "Mensagens"},
        ),
    ]
