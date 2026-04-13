import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { API_ENDPOINTS } from '../config/api';
import { httpGet } from './httpClient';
import plantasOfflineService from './plantasOfflineService';
import { OFFLINE_KEYS, obterSpeciesBaseMeta, salvarSpeciesBaseMeta, upsertCollection } from './offlineStorage';

const SELECTED_IDS_KEY = '@offline/species_selected_ids';
const MAX_PROFUNDIDADE = 2;

const hashFromString = (value) => {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = ((hash << 5) - hash) + value.charCodeAt(i);
    hash |= 0;
  }
  return `h${Math.abs(hash)}`;
};

const normalizeText = (value = '') => String(value || '')
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .replace(/\s+/g, ' ')
  .trim()
  .toLowerCase();

const normalizeArray = (values = []) => {
  const list = Array.isArray(values) ? values : [values];
  const map = new Map();
  for (const raw of list) {
    const txt = String(raw || '').trim();
    const key = normalizeText(txt);
    if (!txt || !key || map.has(key)) continue;
    map.set(key, txt);
  }
  return Array.from(map.values());
};

const isValidIdentifier = (value) => value !== null && value !== undefined && String(value).trim() !== '';

const scoreFonte = (item) => {
  const fonte = normalizeText(item?.fonte_resultado || item?.origem_integracao || '');
  if (fonte.includes('referencial')) return 4;
  if (fonte.includes('gbif')) return 3;
  if (fonte.includes('inaturalist')) return 2;
  return 1;
};

const scoreCompletude = (item = {}) => {
  const fields = [
    'nome_popular', 'nome_cientifico', 'familia', 'parte_comestivel', 'forma_uso',
    'frutificacao', 'colheita', 'bioma', 'regiao', 'origem_integracao',
  ];
  let score = fields.reduce((sum, f) => sum + (item[f] ? 1 : 0), 0);
  score += (item.sinonimos || []).length * 0.1;
  score += (item.nomes_populares || []).length * 0.1;
  return score;
};

class SpeciesFocusService {
  gerarStableId(especie = {}) {
    if (isValidIdentifier(especie.id)) return `id:${String(especie.id).trim()}`;
    if (isValidIdentifier(especie.plataforma_id)) return `pid:${String(especie.plataforma_id).trim()}`;

    const nomeCientificoNorm = normalizeText(especie.nome_cientifico || especie.nome_cientifico_valido || '');
    if (nomeCientificoNorm) return `nc:${hashFromString(nomeCientificoNorm)}`;

    const nomePopularNorm = normalizeText(especie.nome_popular || (especie.nomes_populares || [])[0] || '');
    if (nomePopularNorm) return `np:${hashFromString(nomePopularNorm)}`;

    const payloadMinimo = JSON.stringify({
      fonte: normalizeText(especie.fonte_resultado || especie.origem_integracao || ''),
      sinonimos: normalizeArray(especie.sinonimos || []).slice(0, 3).map(normalizeText),
      nomes_populares: normalizeArray(especie.nomes_populares || []).slice(0, 3).map(normalizeText),
      familia: normalizeText(especie.familia || ''),
    });
    return `payload:${hashFromString(payloadMinimo)}`;
  }

  prepararEspecieParaOffline(especie = {}) {
    const nomesPopulares = normalizeArray(especie.nomes_populares || [especie.nome_popular]);
    const sinonimos = normalizeArray(especie.sinonimos || []);
    const nomeCientifico = String(especie.nome_cientifico || especie.nome_cientifico_valido || '').trim();
    const idOriginal = isValidIdentifier(especie.id) ? String(especie.id).trim() : null;
    const plataformaIdOriginal = isValidIdentifier(especie.plataforma_id) ? String(especie.plataforma_id).trim() : null;
    const internalId = isValidIdentifier(especie.internal_id) ? String(especie.internal_id).trim() : null;
    const externalId = isValidIdentifier(especie.external_id) ? String(especie.external_id).trim() : null;
    const downloadIdOriginal = isValidIdentifier(especie.download_id) ? String(especie.download_id).trim() : null;
    const stable_id = this.gerarStableId({ ...especie, nome_cientifico: nomeCientifico, nomes_populares: nomesPopulares, sinonimos });
    const idFinal = idOriginal || plataformaIdOriginal || stable_id;

    return {
      id: idFinal,
      stable_id,
      plataforma_id: plataformaIdOriginal || idOriginal || null,
      internal_id: internalId || (idOriginal && /^-?\d+$/.test(idOriginal) ? idOriginal : null),
      external_id: externalId || (idOriginal && !/^-?\d+$/.test(idOriginal) ? idOriginal : null),
      download_id: downloadIdOriginal || internalId || idOriginal || plataformaIdOriginal || externalId || stable_id,
      nome_popular: String(especie.nome_popular || nomesPopulares[0] || '').trim(),
      nome_cientifico: nomeCientifico,
      nomes_populares: nomesPopulares,
      sinonimos,
      familia: especie.familia || '',
      parte_comestivel: especie.parte_comestivel || '',
      forma_uso: especie.forma_uso || '',
      frutificacao: especie.frutificacao || especie.epoca_frutificacao || '',
      colheita: especie.colheita || especie.epoca_colheita || '',
      bioma: especie.bioma || '',
      regiao: especie.regiao || especie.regiao_ocorrencia || '',
      origem_integracao: especie.origem_integracao || especie.origem || 'colaborapanc',
      metadados_reconhecimento: especie.metadados_reconhecimento || {
        relevancia: Number(especie.relevancia || especie.score || 0),
        fontes_dados: normalizeArray(especie.fontes_dados || [especie.fonte_resultado]),
      },
      tamanho_estimado_mb: Number(especie.tamanho_estimado_mb || 0.5),
      versao_base: especie.versao_base || especie.versao || '1',
      limiar_confianca: Number(especie.limiar_confianca || especie.confianca_minima || 0.65),
      fonte_resultado: especie.fonte_resultado || 'online_integracao',
      ja_baixada: Boolean(especie.ja_baixada),
      disponivel_offline: Boolean(especie.disponivel_offline || especie.ja_baixada),
      disponivel_para_offline: Boolean(especie.disponivel_para_offline ?? true),
      tem_modelo_ar: Boolean(especie.tem_modelo_ar),
      num_variacoes: Number(especie.num_variacoes || 0),
      grupo_taxonomico: especie.grupo_taxonomico || '',
      regiao_ocorrencia: especie.regiao_ocorrencia || especie.regiao || '',
      epoca_frutificacao: especie.epoca_frutificacao || especie.frutificacao || '',
      epoca_colheita: especie.epoca_colheita || especie.colheita || '',
    };
  }

  normalizarListaParaUI(itens = [], { fontePadrao = 'desconhecida' } = {}) {
    return (Array.isArray(itens) ? itens : [])
      .map((item) => this.prepararEspecieParaOffline({ ...item, fonte_resultado: item?.fonte_resultado || fontePadrao }))
      .filter((item) => isValidIdentifier(item.stable_id) || isValidIdentifier(item.id));
  }

  consolidarResultadosEspecies(resultados = []) {
    const mapa = new Map();

    for (const raw of (Array.isArray(resultados) ? resultados : [])) {
      const especie = this.prepararEspecieParaOffline(raw);
      if (!isValidIdentifier(especie.stable_id) && !isValidIdentifier(especie.id)) continue;

      const chaveNome = normalizeText(especie.nome_cientifico || '');
      const chavePid = normalizeText(especie.plataforma_id || '');
      const key = chaveNome
        ? `nc:${chaveNome}`
        : (chavePid ? `pid:${chavePid}` : `sid:${especie.stable_id}`);

      const atual = mapa.get(key);
      if (!atual) {
        mapa.set(key, especie);
        continue;
      }

      const preferirNova = scoreFonte(especie) > scoreFonte(atual)
        || (scoreFonte(especie) === scoreFonte(atual) && scoreCompletude(especie) > scoreCompletude(atual));

      const base = preferirNova ? especie : atual;
      const extra = preferirNova ? atual : especie;

      mapa.set(key, {
        ...base,
        id: base.id || extra.id,
        stable_id: base.stable_id || extra.stable_id,
        download_id: base.download_id || extra.download_id,
        internal_id: base.internal_id || extra.internal_id,
        external_id: base.external_id || extra.external_id,
        plataforma_id: base.plataforma_id || extra.plataforma_id,
        nome_popular: base.nome_popular || extra.nome_popular,
        nome_cientifico: base.nome_cientifico || extra.nome_cientifico,
        nomes_populares: normalizeArray([...(base.nomes_populares || []), ...(extra.nomes_populares || [])]),
        sinonimos: normalizeArray([...(base.sinonimos || []), ...(extra.sinonimos || [])]),
        familia: base.familia || extra.familia,
        parte_comestivel: base.parte_comestivel || extra.parte_comestivel,
        forma_uso: base.forma_uso || extra.forma_uso,
        frutificacao: base.frutificacao || extra.frutificacao,
        colheita: base.colheita || extra.colheita,
        bioma: base.bioma || extra.bioma,
        regiao: base.regiao || extra.regiao,
        origem_integracao: base.origem_integracao || extra.origem_integracao,
        metadados_reconhecimento: {
          ...(extra.metadados_reconhecimento || {}),
          ...(base.metadados_reconhecimento || {}),
          fontes_dados: normalizeArray([
            ...((base.metadados_reconhecimento || {}).fontes_dados || []),
            ...((extra.metadados_reconhecimento || {}).fontes_dados || []),
            base.fonte_resultado,
            extra.fonte_resultado,
          ]),
        },
        fonte_resultado: base.fonte_resultado || extra.fonte_resultado,
        limiar_confianca: Math.max(base.limiar_confianca || 0, extra.limiar_confianca || 0),
        ja_baixada: Boolean(base.ja_baixada || extra.ja_baixada),
        disponivel_offline: Boolean(base.disponivel_offline || extra.disponivel_offline),
      });
    }

    return Array.from(mapa.values())
      .filter((item) => isValidIdentifier(item.stable_id) || isValidIdentifier(item.id))
      .sort((a, b) => {
        const scoreA = scoreFonte(a) * 100 + scoreCompletude(a) + (a.metadados_reconhecimento?.relevancia || 0);
        const scoreB = scoreFonte(b) * 100 + scoreCompletude(b) + (b.metadados_reconhecimento?.relevancia || 0);
        return scoreB - scoreA;
      });
  }

  async buscarEspeciesOfflineLocal({ busca = '' } = {}) {
    const termo = normalizeText(String(busca || ''));
    const raw = await AsyncStorage.getItem(OFFLINE_KEYS.SPECIES_FOCUS);
    const especies = JSON.parse(raw || '[]');

    const baseNormalizada = this.normalizarListaParaUI(especies, { fontePadrao: 'offline_referencial' });

    if (!termo) {
      const consolidadas = this.consolidarResultadosEspecies(baseNormalizada);
      return {
        especies: consolidadas,
        total: consolidadas.length,
        fonte_resultado: 'offline_referencial',
      };
    }

    const filtradas = baseNormalizada.filter((item) => {
      const campos = normalizeArray([
        item.nome_popular,
        item.nome_cientifico,
        ...(item.nomes_populares || []),
        ...(item.sinonimos || []),
      ]).map((v) => normalizeText(v));
      return campos.some((c) => c.includes(termo));
    });

    const consolidadas = this.consolidarResultadosEspecies(filtradas);
    return { especies: consolidadas, total: consolidadas.length, fonte_resultado: 'offline_referencial' };
  }

  async buscarEspeciesReferenciais({ busca = '', filtros = {} } = {}) {
    const termoBusca = String(busca || '').trim();
    if (!termoBusca) return { especies: [], total: 0, fonte_resultado: 'online_integracao' };

    const params = new URLSearchParams({ q: termoBusca, limite: String(filtros?.limite || 50) });
    const payload = await httpGet(`${API_ENDPOINTS.especiesReferenciaisBusca}?${params.toString()}`);
    const normalizadas = this.normalizarListaParaUI(payload?.especies || [], { fontePadrao: 'referencial_interna' });
    const consolidadas = this.consolidarResultadosEspecies(normalizadas);
    return { especies: consolidadas, total: consolidadas.length, fonte_resultado: 'referencial_interna' };
  }

  async buscarEspeciesRecursivamente({ busca = '', filtros = {}, limite = 50 } = {}) {
    const termo = String(busca || '').trim();
    if (!termo) return { especies: [], total: 0, fonte_resultado: 'online_integracao' };

    const netInfo = await NetInfo.fetch();
    const online = Boolean(netInfo?.isConnected && netInfo?.isInternetReachable !== false);
    if (!online) {
      return this.buscarEspeciesOfflineLocal({ busca: termo });
    }

    const visitados = new Set();
    const fila = [{ termo, profundidade: 0 }];
    const resultados = [];

    while (fila.length > 0 && resultados.length < limite) {
      const atual = fila.shift();
      const termoAtual = String(atual?.termo || '').trim();
      const termoNorm = normalizeText(termoAtual);
      if (!termoNorm || visitados.has(termoNorm)) continue;
      visitados.add(termoNorm);

      const params = new URLSearchParams({
        q: termoAtual,
        limite: String(limite),
        profundidade_max: String(MAX_PROFUNDIDADE),
      });

      const [canonico, recursivo] = await Promise.allSettled([
        httpGet(`${API_ENDPOINTS.especiesReferenciaisBusca}?${params.toString()}`),
        httpGet(`${API_ENDPOINTS.especiesReferenciaisBuscaRecursiva}?${params.toString()}`),
      ]);

      const coletaBruta = [];
      if (canonico.status === 'fulfilled') coletaBruta.push(...(canonico.value?.especies || []));
      if (recursivo.status === 'fulfilled') coletaBruta.push(...(recursivo.value?.especies || []));
      const coleta = this.normalizarListaParaUI(coletaBruta, { fontePadrao: 'online_integracao_recursiva' });

      resultados.push(...coleta);

      if (atual.profundidade < MAX_PROFUNDIDADE) {
        const consolidadosParcial = this.consolidarResultadosEspecies(coleta);
        const expandidos = [];
        for (const item of consolidadosParcial) {
          expandidos.push(item.nome_cientifico);
          expandidos.push(...(item.sinonimos || []).slice(0, 3));
          expandidos.push(...(item.nomes_populares || []).slice(0, 2));
        }
        for (const termoExpandido of expandidos) {
          const key = normalizeText(String(termoExpandido || ''));
          if (!key || visitados.has(key)) continue;
          fila.push({ termo: termoExpandido, profundidade: atual.profundidade + 1 });
        }
      }

      if (visitados.size > limite * 2) break;
    }

    const consolidadas = this.consolidarResultadosEspecies(resultados).slice(0, limite);
    return {
      especies: consolidadas,
      total: consolidadas.length,
      fonte_resultado: 'online_integracao_recursiva',
    };
  }

  async listarEspeciesDisponiveis({ busca = '', filtros = {} } = {}) {
    const termo = String(busca || '').trim();
    if (termo.length < 2) return [];

    const payload = await this.buscarEspeciesRecursivamente({ busca: termo, filtros });
    return payload.especies || [];
  }

  async salvarSelecao(ids) {
    await AsyncStorage.setItem(SELECTED_IDS_KEY, JSON.stringify(ids));
  }

  async obterSelecao() {
    return JSON.parse(await AsyncStorage.getItem(SELECTED_IDS_KEY) || '[]');
  }

  async estimarPacote(ids, especiesDisponiveis = []) {
    const setIds = new Set(ids);
    const selecionadas = especiesDisponiveis.filter((item) => setIds.has(item.stable_id || item.id));
    const tamanhoMb = selecionadas.reduce((sum, item) => sum + (item.tamanho_estimado_mb || 0), 0);
    return { quantidade: selecionadas.length, tamanhoMb: Number(tamanhoMb.toFixed(2)) };
  }

  async baixarBaseSelecionada({ ids, especiesDisponiveis, configuracao = {} }) {
    if (!ids?.length) {
      throw new Error('Selecione ao menos uma espécie para baixar');
    }

    const idsSelecionados = new Set(ids.map((id) => String(id)));
    const especiesSelecionadas = (especiesDisponiveis || []).filter((item) => idsSelecionados.has(String(item.stable_id || item.id)));
    const downloadIds = especiesSelecionadas.map((item) => item.download_id).filter((id) => isValidIdentifier(id));

    if (!downloadIds.length) {
      throw new Error('Nenhuma espécie selecionada possui identificador compatível para download');
    }

    const resultadoDownload = await plantasOfflineService.baixarPlantas(downloadIds, {
      incluir_modelos_ar: !!configuracao.incluir_modelos_ar,
      qualidade_fotos: configuracao.qualidade_fotos || 'media',
      itens_selecionados: especiesSelecionadas,
    });

    if (!resultadoDownload.sucesso) {
      throw new Error(resultadoDownload.erro || 'Falha ao baixar base offline');
    }

    const especies = especiesSelecionadas
      .map((item) => this.prepararEspecieParaOffline(item));

    const ordered = especies.sort((a, b) => String(a.stable_id || a.id).localeCompare(String(b.stable_id || b.id)));
    const hash = hashFromString(JSON.stringify(ordered.map((s) => [s.stable_id, s.id, s.nome_cientifico, s.versao_base])));

    await upsertCollection(OFFLINE_KEYS.SPECIES_FOCUS, ordered);

    const meta = {
      status: 'disponivel_offline',
      quantidade: ordered.length,
      tamanho_estimado_mb: Number(ordered.reduce((sum, item) => sum + item.tamanho_estimado_mb, 0).toFixed(2)),
      baixado_em: new Date().toISOString(),
      versao_base: `species-focus-${new Date().toISOString().slice(0, 10)}`,
      hash_integridade: hash,
      limiar_confianca_padrao: Number(configuracao.limiar_confianca_padrao || 0.65),
      selecionadas_ids: ids,
    };

    await salvarSpeciesBaseMeta(meta);
    await this.salvarSelecao(ids);

    return { ...resultadoDownload, meta };
  }

  async removerBaseOffline() {
    await AsyncStorage.removeItem(OFFLINE_KEYS.SPECIES_FOCUS);
    await AsyncStorage.removeItem(SELECTED_IDS_KEY);
    await salvarSpeciesBaseMeta({ status: 'nao_baixada', quantidade: 0 });
  }

  async obterStatusBaseOffline() {
    const meta = await obterSpeciesBaseMeta();
    if (!meta) return { status: 'nao_baixada', quantidade: 0, tamanho_estimado_mb: 0 };
    return meta;
  }
}

export default new SpeciesFocusService();
