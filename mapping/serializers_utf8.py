from rest_framework import serializers
from .models import PontoPANC, AlertaClimatico


class AlertaClimaticoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertaClimatico
        fields = ['tipo', 'descricao', 'data_inicio', 'data_fim', 'fonte']


class PontoPANCSerializer(serializers.ModelSerializer):
    alertas = serializers.SerializerMethodField()

    class Meta:
        model = PontoPANC
        fields = [
            'id', 'nome_popular', 'nome_cientifico', 'tipo_local', 'colaborador',
            'grupo', 'relato', 'foto_url', 'status_validacao', 'localizacao',
            'pode_editar', 'alertas'
        ]

    def get_alertas(self, obj):
        if not obj.localizacao:
            return []
        lat, lon = obj.localizacao
        alertas = AlertaClimatico.objects.filter(
            latitude__range=(lat - 0.5, lat + 0.5),
            longitude__range=(lon - 0.5, lon + 0.5)
        ).order_by('-data_inicio')[:3]
        return AlertaClimaticoSerializer(alertas, many=True).data
