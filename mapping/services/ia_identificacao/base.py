from abc import ABC, abstractmethod
from .schemas import ResultadoInferencia


class BaseIdentificacaoProvider(ABC):
    provider_name = 'base'

    @abstractmethod
    def inferir(self, foto) -> ResultadoInferencia:
        raise NotImplementedError
