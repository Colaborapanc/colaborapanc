from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mapping', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criada_em', models.DateTimeField(auto_now_add=True, verbose_name='Criada em')),
                ('atualizada_em', models.DateTimeField(auto_now=True, verbose_name='Atualizada em')),
                ('participantes', models.ManyToManyField(related_name='conversas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Conversa',
                'verbose_name_plural': 'Conversas',
                'ordering': ['-atualizada_em'],
            },
        ),
        migrations.CreateModel(
            name='IntegracaoEcommerce',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome da integração')),
                ('base_url', models.URLField(verbose_name='URL base')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('ultima_sincronizacao', models.DateTimeField(blank=True, null=True, verbose_name='Última sincronização')),
            ],
            options={
                'verbose_name': 'Integração de e-commerce',
                'verbose_name_plural': 'Integrações de e-commerce',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Notificacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=150, verbose_name='Título')),
                ('mensagem', models.TextField(verbose_name='Mensagem')),
                ('dados', models.JSONField(blank=True, default=dict, verbose_name='Dados extras')),
                ('lida_em', models.DateTimeField(blank=True, null=True, verbose_name='Lida em')),
                ('criada_em', models.DateTimeField(auto_now_add=True, verbose_name='Criada em')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificacoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notificação',
                'verbose_name_plural': 'Notificações',
                'ordering': ['-criada_em'],
            },
        ),
        migrations.CreateModel(
            name='PushNotificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255, unique=True, verbose_name='Token do dispositivo')),
                ('plataforma', models.CharField(choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web'), ('outro', 'Outro')], default='outro', max_length=20, verbose_name='Plataforma')),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Token de push',
                'verbose_name_plural': 'Tokens de push',
                'ordering': ['-atualizado_em'],
            },
        ),
        migrations.CreateModel(
            name='RecomendacaoPANC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(default=0, verbose_name='Score de recomendação')),
                ('origem_modelo', models.CharField(default='baseline', max_length=100, verbose_name='Origem do modelo')),
                ('criada_em', models.DateTimeField(auto_now_add=True, verbose_name='Criada em')),
                ('planta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recomendacoes', to='mapping.plantareferencial')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recomendacoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Recomendação PANC',
                'verbose_name_plural': 'Recomendações PANC',
                'ordering': ['-criada_em'],
            },
        ),
        migrations.CreateModel(
            name='ReferenciaAR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120, verbose_name='Título')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('asset_url', models.URLField(blank=True, verbose_name='URL do asset')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('planta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referencias_ar', to='mapping.plantareferencial')),
            ],
            options={
                'verbose_name': 'Referência AR',
                'verbose_name_plural': 'Referências AR',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='RoteiroPANC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=120, verbose_name='Título')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('criador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roteiros', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Roteiro PANC',
                'verbose_name_plural': 'Roteiros PANC',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='Mensagem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField(verbose_name='Texto')),
                ('lida_em', models.DateTimeField(blank=True, null=True, verbose_name='Lida em')),
                ('criada_em', models.DateTimeField(auto_now_add=True, verbose_name='Criada em')),
                ('conversa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensagens', to='mapping.conversa')),
                ('remetente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensagens_enviadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mensagem',
                'verbose_name_plural': 'Mensagens',
                'ordering': ['criada_em'],
            },
        ),
        migrations.CreateModel(
            name='ProdutoSemente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150, verbose_name='Nome do produto')),
                ('url', models.URLField(verbose_name='URL do produto')),
                ('preco', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Preço')),
                ('disponivel', models.BooleanField(default=True, verbose_name='Disponível')),
                ('integracao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='produtos', to='mapping.integracaoecommerce')),
                ('planta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='produtos_semente', to='mapping.plantareferencial')),
            ],
            options={
                'verbose_name': 'Produto de semente',
                'verbose_name_plural': 'Produtos de sementes',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='RoteiroPANCItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ordem', models.PositiveIntegerField(default=1, verbose_name='Ordem')),
                ('observacao', models.CharField(blank=True, max_length=200, verbose_name='Observação')),
                ('ponto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roteiros', to='mapping.pontopanc')),
                ('roteiro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='mapping.roteiropanc')),
            ],
            options={
                'verbose_name': 'Item do roteiro',
                'verbose_name_plural': 'Itens do roteiro',
                'ordering': ['ordem'],
                'unique_together': {('roteiro', 'ponto')},
            },
        ),
        migrations.CreateModel(
            name='CompartilhamentoSocial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('canal', models.CharField(choices=[('whatsapp', 'WhatsApp'), ('instagram', 'Instagram'), ('facebook', 'Facebook'), ('twitter', 'X/Twitter'), ('email', 'E-mail'), ('outro', 'Outro')], default='outro', max_length=20, verbose_name='Canal')),
                ('url_compartilhada', models.URLField(blank=True, verbose_name='URL compartilhada')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('ponto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compartilhamentos', to='mapping.pontopanc')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compartilhamentos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Compartilhamento social',
                'verbose_name_plural': 'Compartilhamentos sociais',
                'ordering': ['-criado_em'],
            },
        ),
    ]
