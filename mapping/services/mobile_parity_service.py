import hashlib
from dataclasses import dataclass

from django.db.models import Max, Q

from mapping.identificacao_avancada import identificar_planta as identificar_planta_avancada
from mapping.models import PlantaCustomizada, PlantaReferencial, PontoPANC
from mapping.services.plant_identification_service import PlantIdentificationService


@dataclass
class IdentificacaoNormalizada:
    sucesso: bool
    payload: dict


class MobileParityService:
    """
    Serviço canônico para contratos web/mobile.
    Centraliza pipeline de identificação, payload de mapa e exportação offline.
    """

    def __init__(self):
        self.identificador_web = PlantIdentificationService()

    def identificar_por_imagem(self, imagem, *, usar_custom_db=True, usar_google=True):
        identificacao_web = self.identificador_web.identify(foto=imagem)
        melhor = {
            "nome_popular": identificacao_web.nome_popular or "",
            "nome_cientifico": identificacao_web.nome_cientifico or "",
            "score": float(identificacao_web.score or 0.0),
            "metodo": identificacao_web.fonte or "pipeline_web",
            "candidatos": identificacao_web.candidatos or [],
        }

        if hasattr(imagem, "seek"):
            imagem.seek(0)

        # Pipeline avançado entra como apoio da pipeline web
        if melhor["score"] < 0.55:
            advanced = identificar_planta_avancada(
                imagem,
                usar_custom_db=usar_custom_db,
                usar_google=usar_google,
            )
            advanced_score = float((advanced or {}).get("score", 0.0) or 0.0)
            if advanced_score > melhor["score"]:
                melhor = {
                    "nome_popular": advanced.get("nome_popular", ""),
                    "nome_cientifico": advanced.get("nome_cientifico", ""),
                    "score": advanced_score,
                    "metodo": advanced.get("metodo", "pipeline_avancada"),
                    "candidatos": melhor["candidatos"],
                    "planta_base_id": advanced.get("planta_base_id"),
                    "planta_customizada_id": advanced.get("planta_customizada_id"),
                }

        planta = None
        if melhor.get("planta_base_id"):
            planta = PlantaReferencial.objects.filter(id=melhor["planta_base_id"]).first()
        if not planta:
            planta, _ = self.identificador_web.resolve_or_create_planta(
                nome_popular=melhor.get("nome_popular", ""),
                nome_cientifico=melhor.get("nome_cientifico", ""),
                identification=identificacao_web,
            )

        payload = self._montar_payload_identificacao(melhor, planta)
        return IdentificacaoNormalizada(sucesso=payload["sucesso"], payload=payload)

    def _montar_payload_identificacao(self, melhor, planta):
        enriquecimento_status = (planta.status_enriquecimento if planta else "") or "pendente"
        precisa_revisao = melhor.get("score", 0.0) < 0.65

        return {
            "sucesso": melhor.get("score", 0.0) >= 0.5,
            "metodo": melhor.get("metodo", "nenhum"),
            "nome_popular": melhor.get("nome_popular", ""),
            "nome_cientifico": melhor.get("nome_cientifico", ""),
            "score": melhor.get("score", 0.0),
            "planta_base_id": planta.id if planta else melhor.get("planta_base_id"),
            "planta_customizada_id": melhor.get("planta_customizada_id"),
            "fontes_identificacao": [c.get("fonte") for c in (melhor.get("candidatos") or []) if c.get("fonte")],
            "parte_comestivel": (planta.parte_comestivel if planta else "") or "",
            "forma_uso": (planta.forma_uso if planta else "") or "",
            "epoca_frutificacao": (planta.epoca_frutificacao if planta else "") or "",
            "epoca_colheita": (planta.epoca_colheita if planta else "") or "",
            "grupo_taxonomico": (planta.grupo_taxonomico if planta else "") or "",
            "bioma": (planta.bioma if planta else "") or "",
            "status_enriquecimento": enriquecimento_status,
            "validacao_pendente_revisao_humana": precisa_revisao,
            "candidatos": melhor.get("candidatos", []),
        }

    def listar_previews_mapa(self, *, termo=None, limite=400):
        qs = PontoPANC.objects.select_related("planta").order_by("-criado_em")
        if termo:
            qs = qs.filter(
                Q(nome_popular__icontains=termo)
                | Q(nome_cientifico_sugerido__icontains=termo)
                | Q(planta__nome_popular__icontains=termo)
                | Q(planta__nome_cientifico__icontains=termo)
            )
        itens = []
        for ponto in qs[:limite]:
            if ponto.localizacao:
                localizacao = {"type": "Point", "coordinates": [ponto.localizacao.x, ponto.localizacao.y]}
            elif ponto.longitude is not None and ponto.latitude is not None:
                localizacao = {"type": "Point", "coordinates": [ponto.longitude, ponto.latitude]}
            else:
                localizacao = None
            itens.append({
                "id": ponto.id,
                "detalhe_id": ponto.id,
                "nome_popular": ponto.planta.nome_popular if ponto.planta_id else (ponto.nome_popular or ""),
                "nome_cientifico": (ponto.planta.nome_cientifico if ponto.planta_id else ponto.nome_cientifico_sugerido) or "",
                "cidade": ponto.cidade or "",
                "estado": ponto.estado or "",
                "tipo_local": ponto.tipo_local or "",
                "status_validacao": ponto.status_validacao or "pendente",
                "comestibilidade_confirmada": bool(ponto.comestibilidade_confirmada),
                "comestibilidade_status": ponto.comestibilidade_status or "indeterminado",
                "parte_comestivel_confirmada": bool(ponto.parte_comestivel_confirmada),
                "parte_comestivel": ", ".join(ponto.parte_comestivel_lista or []),
                "frutificacao_confirmada": bool(ponto.frutificacao_confirmada),
                "frutificacao": ", ".join(ponto.frutificacao_meses or []),
                "colheita_confirmada": bool(ponto.colheita_confirmada),
                "colheita": ", ".join(ponto.colheita_periodo) if isinstance(ponto.colheita_periodo, list) else (ponto.colheita_periodo or ""),
                "localizacao": localizacao,
                "hint": "Toque para ver detalhes",
            })
        return itens

    def metadata_base_offline(self):
        total = PlantaReferencial.objects.count()
        max_hist = PlantaReferencial.objects.aggregate(mx=Max("historico_enriquecimento__data")).get("mx")
        version_seed = f"{total}:{max_hist.isoformat() if max_hist else 'none'}"
        versao = hashlib.sha1(version_seed.encode("utf-8")).hexdigest()[:12]
        return {
            "versao": versao,
            "total_especies": total,
            "gerado_em": max_hist.isoformat() if max_hist else None,
        }

    def exportar_base_offline(self, *, limite=500, busca=None):
        plantas = PlantaReferencial.objects.all().order_by("nome_popular")
        if busca:
            plantas = plantas.filter(
                Q(nome_popular__icontains=busca) |
                Q(nome_cientifico__icontains=busca) |
                Q(nome_cientifico_valido__icontains=busca)
            )

        especies = []
        for planta in plantas[:limite]:
            variacoes = PlantaCustomizada.objects.filter(
                planta_base=planta,
                validado_por_especialista=True,
            )[:8]
            especies.append({
                "id": planta.id,
                "nome_popular": planta.nome_popular,
                "nome_cientifico": planta.nome_cientifico,
                "nome_cientifico_valido": planta.nome_cientifico_valido or "",
                "sinonimos": planta.sinonimos or [],
                "nomes_populares": planta.nomes_populares or [planta.nome_popular],
                "aliases": planta.aliases or [],
                "parte_comestivel": planta.parte_comestivel or "",
                "forma_uso": planta.forma_uso or "",
                "epoca_frutificacao": planta.epoca_frutificacao or "",
                "epoca_colheita": planta.epoca_colheita or "",
                "familia": planta.familia or "",
                "grupo_taxonomico": planta.grupo_taxonomico or "",
                "bioma": planta.bioma or "",
                "regiao_ocorrencia": planta.regiao_ocorrencia or "",
                "status_enriquecimento": planta.status_enriquecimento or "pendente",
                "nivel_confianca_enriquecimento": float(planta.nivel_confianca_enriquecimento or 0.0),
                "variacoes": [
                    {
                        "id": v.id,
                        "nome_variacao": v.nome_variacao,
                        "features_ml": v.features_ml or {},
                    }
                    for v in variacoes
                ],
            })

        return {
            "metadata": self.metadata_base_offline(),
            "especies": especies,
        }
