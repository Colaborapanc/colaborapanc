from django import forms
from leaflet.forms.widgets import LeafletWidget
from .models import (
    PontoPANC, PlantaReferencial, Grupo, Badge, Feedback, Missao, SugestaoMissao
)
from django.core.exceptions import ValidationError

# =========================
# Formulário principal para cadastro/edição de ponto PANC
# =========================

class PontoPANCForm(forms.ModelForm):
    """Formulário principal para cadastro/edição de ponto PANC."""

    nome_popular = forms.CharField(
        label="Nome popular da planta",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'list': 'datalist-nome-popular',
            'id': 'id_nome_popular',
            'autocomplete': 'off',
            'placeholder': 'Ex: Taioba',
            'autofocus': True,
        }),
        help_text="Digite ao menos 2 letras para buscar automaticamente.",
    )
    nome_cientifico = forms.CharField(
        label="Nome científico",
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_nome_cientifico',
            'placeholder': 'Será preenchido automaticamente (pode editar)',
        }),
    )
    comestibilidade_status = forms.ChoiceField(
        label="Comestível",
        required=False,
        choices=(
            ("indeterminado", "Não informado"),
            ("sim", "Sim"),
            ("nao", "Não"),
        ),
        initial="indeterminado",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_comestibilidade_status"}),
    )
    parte_comestivel_manual = forms.CharField(
        label="Parte comestível",
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "id_parte_comestivel_manual",
                "placeholder": "Ex: folha, fruto",
            }
        ),
    )
    frutificacao_manual = forms.CharField(
        label="Frutificação",
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "id_frutificacao_manual",
                "placeholder": "Ex: jan, fev, mar",
            }
        ),
    )
    colheita_manual = forms.CharField(
        label="Colheita",
        required=False,
        widget=forms.TextInput(
            attrs={
                "id": "id_colheita_manual",
                "placeholder": "Ex: abr a jul",
            }
        ),
    )
    grupo = forms.ModelChoiceField(
        label="Grupo/Comunidade",
        queryset=Grupo.objects.all(),
        required=False,
        help_text="(Opcional) Selecione o grupo/comunidade desta contribuição.",
        widget=forms.Select(attrs={
            'id': 'id_grupo',
            'class': 'form-select',
        }),
    )
    cidade = forms.CharField(
        label="Cidade",
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_cidade',
            'placeholder': 'Preenchido automaticamente (pode editar)',
        }),
    )
    estado = forms.CharField(
        label="Estado",
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_estado',
            'placeholder': 'Preenchido automaticamente (pode editar)',
        }),
    )
    bairro = forms.CharField(
        label="Bairro",
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_bairro',
            'placeholder': 'Preenchido automaticamente (pode editar)',
        }),
    )
    numero = forms.CharField(
        label="Número",
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_numero',
            'placeholder': 'Número (opcional)',
        }),
    )

    class Meta:
        model = PontoPANC
        fields = [
            'nome_popular', 'nome_cientifico', 'tipo_local', 'endereco',
            'numero', 'bairro', 'cidade', 'estado', 'colaborador',
            'relato', 'foto', 'localizacao', 'grupo'
        ]
        widgets = {
            'tipo_local': forms.Select(attrs={'id': 'id_tipo_local', 'class': 'form-select'}),
            'endereco': forms.TextInput(attrs={'id': 'id_endereco', 'placeholder': 'Preenchido automaticamente (pode editar)'}),
            'colaborador': forms.TextInput(attrs={'id': 'id_colaborador', 'placeholder': 'Seu nome ou apelido'}),
            'relato': forms.Textarea(attrs={'rows': 4, 'id': 'id_relato', 'placeholder': 'Conte algo sobre o ponto, a planta ou o uso tradicional.'}),
            'foto': forms.ClearableFileInput(attrs={'id': 'id_foto', 'class': 'form-control', 'accept': 'image/*'}),
            'localizacao': forms.HiddenInput(attrs={'id': 'id_localizacao'}),
        }

    def __init__(self, *args, **kwargs):
        """Garante IDs corretos mesmo se sobrescritos por prefixos do Django."""
        super().__init__(*args, **kwargs)
        # IDs essenciais para integração com JS
        id_fields = [
            'localizacao', 'bairro', 'cidade', 'estado', 'endereco', 'colaborador',
            'relato', 'foto', 'grupo', 'numero', 'tipo_local', 'nome_popular', 'nome_cientifico'
        ]
        for f in id_fields:
            if f in self.fields:
                self.fields[f].widget.attrs['id'] = f"id_{f}"

        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            self.fields["comestibilidade_status"].initial = instance.comestibilidade_status or "indeterminado"
            self.fields["parte_comestivel_manual"].initial = ", ".join(instance.parte_comestivel_lista or [])
            self.fields["frutificacao_manual"].initial = ", ".join(instance.frutificacao_meses or [])
            if isinstance(instance.colheita_periodo, list):
                self.fields["colheita_manual"].initial = ", ".join(instance.colheita_periodo)
            else:
                self.fields["colheita_manual"].initial = instance.colheita_periodo or ""

    def clean_localizacao(self):
        """Valida se a localização foi informada."""
        localizacao = self.cleaned_data.get('localizacao')
        if not localizacao:
            raise ValidationError("Por favor, selecione a localização clicando no mapa.")
        return localizacao

    def clean_nome_popular(self):
        nome = self.cleaned_data.get("nome_popular")
        if nome and len(nome.strip()) < 2:
            raise ValidationError("Digite ao menos 2 letras.")
        return nome.strip() if nome else nome

    def clean(self):
        cleaned_data = super().clean()
        nome_popular = (cleaned_data.get("nome_popular") or "").strip()
        nome_cientifico = (cleaned_data.get("nome_cientifico") or "").strip()
        foto = cleaned_data.get("foto")

        if not nome_popular and not nome_cientifico and not foto:
            raise ValidationError(
                "Informe nome popular, nome científico ou envie uma foto para identificação."
            )

        if nome_popular:
            planta = PlantaReferencial.objects.filter(
                nome_popular__iexact=nome_popular.strip()
            ).first()
            if planta:
                cleaned_data['nome_cientifico'] = planta.nome_cientifico

        cleaned_data["nome_popular"] = nome_popular
        cleaned_data["nome_cientifico"] = nome_cientifico or cleaned_data.get("nome_cientifico", "")
        return cleaned_data

# =========================
# Formulário para filtro de pontos (painéis, revisões, contribuições)
# =========================
class FiltroPontoForm(forms.Form):
    nome_popular = forms.CharField(label="Nome popular", max_length=100, required=False)
    cidade = forms.CharField(label="Cidade", max_length=100, required=False)
    grupo = forms.ModelChoiceField(label="Grupo/Comunidade", queryset=Grupo.objects.all(), required=False)
    status_validacao = forms.ChoiceField(
        label="Status de Validação",
        choices=[
            ('', 'Todos'),
            ('pendente', 'Em validação'),
            ('aprovado', 'Aprovado'),
            ('reprovado', 'Reprovado'),
            ('pendencia', 'Pendência'),
        ],
        required=False
    )

# =========================
# Formulário de grupo/comunidade
# =========================
class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nome', 'descricao']

# =========================
# Formulário de gamificação: badge/conquista
# =========================
class BadgeForm(forms.ModelForm):
    usuarios = forms.ModelMultipleChoiceField(
        queryset=Grupo._meta.get_field('membros').related_model.objects.all(),
        widget=forms.SelectMultiple,
        label="Usuários",
        required=True,
        help_text="Selecione os usuários que receberão esta insígnia."
    )

    class Meta:
        model = Badge
        fields = ['nome', 'descricao', 'icone', 'usuarios', 'nivel', 'missao']

# =========================
# Filtro de ranking para painel de gamificação
# =========================
class RankingFiltroForm(forms.Form):
    periodo = forms.ChoiceField(
        label="Período",
        choices=[
            ('all', 'Geral'),
            ('month', 'Últimos 30 dias'),
            ('week', 'Últimos 7 dias'),
        ],
        required=False
    )
    grupo = forms.ModelChoiceField(label="Grupo/Comunidade", queryset=Grupo.objects.all(), required=False)

# =========================
# Formulário para feedback/sugestão
# =========================
class FeedbackForm(forms.ModelForm):
    email = forms.EmailField(label="Seu e-mail (opcional)", required=False)
    class Meta:
        model = Feedback
        fields = ['mensagem']

# =========================
# Missao
# =========================       
class MissaoForm(forms.ModelForm):
    class Meta:
        model = Missao
        fields = ['titulo', 'descricao', 'tipo', 'pontos', 'meta']

# =========================
# Sugestao Missao
# =========================       
class SugestaoMissaoForm(forms.ModelForm):
    class Meta:
        model = SugestaoMissao
        fields = ['titulo', 'descricao']
