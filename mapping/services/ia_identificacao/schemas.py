from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class PredicaoNormalizada:
    nome_popular: str
    nome_cientifico: str
    score: float
    fonte: str


@dataclass
class ResultadoInferencia:
    sucesso: bool
    provedor: str
    predicoes: List[PredicaoNormalizada]
    confianca_geral: float
    faixa_confianca: str
    justificativa: str
    recomendacao_operacional: str
    requer_revisao_humana: bool
    erro: str = ""
    bruto: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sucesso': self.sucesso,
            'provedor': self.provedor,
            'predicoes': [asdict(p) for p in self.predicoes],
            'confianca_geral': self.confianca_geral,
            'faixa_confianca': self.faixa_confianca,
            'justificativa': self.justificativa,
            'recomendacao_operacional': self.recomendacao_operacional,
            'requer_revisao_humana': self.requer_revisao_humana,
            'erro': self.erro,
        }
