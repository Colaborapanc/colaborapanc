"""
Pacote de enriquecimento.

Importante: evitar imports pesados no módulo de pacote para não criar
import circular com os serviços de biodiversidade/taxonomia.
"""

__all__ = ["PlantaEnrichmentPipeline"]


def __getattr__(name):
    if name == "PlantaEnrichmentPipeline":
        from .planta_enrichment_pipeline import PlantaEnrichmentPipeline

        return PlantaEnrichmentPipeline
    raise AttributeError(name)
