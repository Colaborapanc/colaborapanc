# mapping/services/recomendacao_ml.py
# Serviço de Machine Learning para recomendação de PANCs

import logging
from typing import List, Dict
from django.db.models import Count, Q
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point

logger = logging.getLogger(__name__)


class RecomendacaoMLService:
    """
    Serviço de recomendação de PANCs usando técnicas de Machine Learning
    """

    def __init__(self):
        self.pesos = {
            'proximidade_geografica': 0.3,
            'popularidade': 0.2,
            'adequacao_clima': 0.2,
            'facilidade_cultivo': 0.15,
            'similaridade_usuario': 0.15,
        }

    def gerar_recomendacoes(self, usuario, limite=10):
        """
        Gera recomendações personalizadas para um usuário

        Args:
            usuario: Objeto User
            limite: Número máximo de recomendações

        Returns:
            list: Lista de dicionários com planta e score
        """
        from mapping.models import PlantaReferencial, PontoPANC, RecomendacaoPANC

        # Obtém plantas que o usuário já cadastrou
        plantas_cadastradas = PontoPANC.objects.filter(
            criado_por=usuario
        ).values_list('planta_id', flat=True).distinct()

        # Obtém todas as plantas disponíveis (exceto as já cadastradas)
        plantas_disponiveis = PlantaReferencial.objects.exclude(
            id__in=plantas_cadastradas
        )

        ultimo_ponto = PontoPANC.objects.filter(
            criado_por=usuario
        ).order_by('-criado_em').first()

        proximidade_scores = self._mapear_pontos_proximos(ultimo_ponto)

        recomendacoes = []

        for planta in plantas_disponiveis:
            score = self._calcular_score(usuario, planta, ultimo_ponto, proximidade_scores)
            if score > 0:
                recomendacoes.append({
                    'planta': planta,
                    'score': score,
                    'razao': self._gerar_razao(usuario, planta, score)
                })

        # Ordena por score decrescente
        recomendacoes.sort(key=lambda x: x['score'], reverse=True)

        # Salva recomendações no banco de dados
        for rec in recomendacoes[:limite]:
            RecomendacaoPANC.objects.update_or_create(
                usuario=usuario,
                planta=rec['planta'],
                defaults={
                    'score': rec['score'],
                    'razao': rec['razao']
                }
            )

        return recomendacoes[:limite]

    def _calcular_score(self, usuario, planta, ultimo_ponto, proximidade_scores):
        """
        Calcula score de recomendação para uma planta

        Args:
            usuario: Objeto User
            planta: Objeto PlantaReferencial

        Returns:
            float: Score de 0 a 1
        """
        scores = {
            'proximidade_geografica': self._score_proximidade(
                usuario,
                planta,
                ultimo_ponto,
                proximidade_scores,
            ),
            'popularidade': self._score_popularidade(planta),
            'adequacao_clima': self._score_clima(usuario, planta, ultimo_ponto),
            'facilidade_cultivo': self._score_facilidade(planta),
            'similaridade_usuario': self._score_similaridade(usuario, planta),
        }

        # Calcula score ponderado
        score_final = sum(
            scores[key] * self.pesos[key]
            for key in scores
        )

        return min(max(score_final, 0.0), 1.0)

    def _mapear_pontos_proximos(self, ultimo_ponto):
        from mapping.models import PontoPANC

        if not ultimo_ponto or not ultimo_ponto.localizacao:
            return {}

        pontos_proximos = (
            PontoPANC.objects.filter(
                localizacao__distance_lte=(ultimo_ponto.localizacao, D(km=50))
            )
            .values("planta_id")
            .annotate(total=Count("id"))
        )
        return {item["planta_id"]: item["total"] for item in pontos_proximos}

    def _score_proximidade(self, usuario, planta, ultimo_ponto, proximidade_scores):
        """
        Score baseado em proximidade geográfica

        Calcula se existem pontos dessa planta próximos ao usuário
        """
        try:
            if not ultimo_ponto or not ultimo_ponto.localizacao:
                return 0.5  # Neutro se não tiver localização

            pontos_proximos = proximidade_scores.get(planta.id, 0)

            # Normaliza: quanto mais pontos próximos, maior o score
            return min(pontos_proximos / 10.0, 1.0)

        except Exception as e:
            logger.error(f"Erro ao calcular proximidade: {e}")
            return 0.5

    def _score_popularidade(self, planta):
        """
        Score baseado na popularidade da planta (quantos pontos cadastrados)
        """
        from mapping.models import PontoPANC

        total_pontos = PontoPANC.objects.filter(planta=planta).count()

        # Normaliza: plantas com mais pontos são mais populares
        return min(total_pontos / 100.0, 1.0)

    def _score_clima(self, usuario, planta, ultimo_ponto):
        """
        Score baseado na adequação climática da planta para a região do usuário
        """
        try:
            if not ultimo_ponto:
                return 0.5  # Neutro

            estado_usuario = ultimo_ponto.estado

            # Verifica se a planta tem ocorrência nessa região
            if planta.regiao_ocorrencia and estado_usuario:
                if estado_usuario.upper() in planta.regiao_ocorrencia.upper():
                    return 1.0

            # Verifica bioma
            # (simplificado - em produção, usar dados climáticos reais)
            return 0.6

        except Exception as e:
            logger.error(f"Erro ao calcular adequação climática: {e}")
            return 0.5

    def _score_facilidade(self, planta):
        """
        Score baseado na facilidade de cultivo
        (simplificado - em produção, usar dados reais de dificuldade)
        """
        # Plantas mais comuns são geralmente mais fáceis de cultivar
        partes_comestiveis = ['folha', 'fruto', 'raiz', 'flor']

        if planta.parte_comestivel:
            for parte in partes_comestiveis:
                if parte in planta.parte_comestivel.lower():
                    return 0.8

        return 0.5

    def _score_similaridade(self, usuario, planta):
        """
        Score baseado em similaridade com outros usuários

        Usuários que cadastraram plantas similares também cadastraram esta?
        """
        from mapping.models import PontoPANC

        try:
            # Obtém plantas cadastradas pelo usuário
            plantas_usuario = PontoPANC.objects.filter(
                criado_por=usuario
            ).values_list('planta_id', flat=True).distinct()

            if not plantas_usuario:
                return 0.5

            # Encontra outros usuários que cadastraram essas plantas
            usuarios_similares = PontoPANC.objects.filter(
                planta_id__in=plantas_usuario
            ).exclude(
                criado_por=usuario
            ).values_list('criado_por_id', flat=True).distinct()

            # Verifica se esses usuários também cadastraram a planta recomendada
            usuarios_com_planta = PontoPANC.objects.filter(
                planta=planta,
                criado_por_id__in=usuarios_similares
            ).values_list('criado_por_id', flat=True).distinct().count()

            if not usuarios_similares:
                return 0.5

            # Normaliza: percentual de usuários similares que cadastraram
            return usuarios_com_planta / len(usuarios_similares)

        except Exception as e:
            logger.error(f"Erro ao calcular similaridade: {e}")
            return 0.5

    def _gerar_razao(self, usuario, planta, score):
        """
        Gera explicação textual da recomendação

        Args:
            usuario: Objeto User
            planta: Objeto PlantaReferencial
            score: Score calculado

        Returns:
            str: Texto explicativo
        """
        from mapping.models import PontoPANC

        razoes = []

        # Popularidade
        total_pontos = PontoPANC.objects.filter(planta=planta).count()
        if total_pontos > 10:
            razoes.append(f"Popular na comunidade ({total_pontos} pontos cadastrados)")

        # Proximidade
        ultimo_ponto = PontoPANC.objects.filter(
            criado_por=usuario
        ).order_by('-criado_em').first()

        if ultimo_ponto:
            pontos_proximos = PontoPANC.objects.filter(
                planta=planta,
                localizacao__distance_lte=(
                    ultimo_ponto.localizacao,
                    D(km=50)
                )
            ).count()

            if pontos_proximos > 0:
                razoes.append(f"Encontrada próximo à sua região ({pontos_proximos} pontos)")

        # Adequação
        if planta.regiao_ocorrencia:
            razoes.append(f"Adequada para a região {planta.regiao_ocorrencia}")

        # Facilidade
        if planta.parte_comestivel:
            razoes.append(f"Parte comestível: {planta.parte_comestivel}")

        if not razoes:
            return "Recomendada com base no seu perfil"

        return " • ".join(razoes)


# Instância global do serviço
recomendacao_service = RecomendacaoMLService()


# ===================================
# FUNÇÕES AUXILIARES
# ===================================
def atualizar_recomendacoes_usuario(usuario):
    """
    Atualiza recomendações para um usuário específico

    Args:
        usuario: Objeto User
    """
    try:
        recomendacoes = recomendacao_service.gerar_recomendacoes(usuario, limite=15)
        logger.info(f"Recomendações atualizadas para {usuario.username}: {len(recomendacoes)} PANCs")
        return recomendacoes
    except Exception as e:
        logger.error(f"Erro ao atualizar recomendações: {e}")
        return []


def atualizar_recomendacoes_todos_usuarios():
    """
    Atualiza recomendações para todos os usuários ativos
    (use em tarefas agendadas)
    """
    from django.contrib.auth.models import User

    usuarios_ativos = User.objects.filter(is_active=True)

    for usuario in usuarios_ativos:
        try:
            atualizar_recomendacoes_usuario(usuario)
        except Exception as e:
            logger.error(f"Erro ao atualizar recomendações para {usuario.username}: {e}")
