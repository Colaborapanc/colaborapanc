/**
 * Serviço de gerenciamento de plantas offline seletivas
 * Permite baixar, gerenciar e usar plantas específicas offline
 *
 * Usa httpClient centralizado — fonte única de verdade para auth, headers e timeout.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_ENDPOINTS } from '../config/api';
import { httpGet, httpPost, httpPut, httpDelete } from './httpClient';

const KEYS = {
  PLANTAS_BAIXADAS: '@plantas_offline_baixadas',
  CONFIG_OFFLINE: '@config_offline',
  PACOTES: '@pacotes_offline',
  ULTIMA_SYNC: '@plantas_offline_ultima_sync',
  PADROES_IDENTIFICACAO: '@plantas_offline_padroes',
  BASE_REFERENCIAL_CACHE: '@base_referencial_cache',
};

class PlantasOfflineService {
  _normalizarTextoSeguro(texto) {
    if (!texto) return '';
    return String(texto)
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  _hashDeterministico(valor = '') {
    let hash = 0;
    const txt = String(valor || '');
    for (let i = 0; i < txt.length; i += 1) {
      hash = ((hash << 5) - hash) + txt.charCodeAt(i);
      hash |= 0;
    }
    return `h${Math.abs(hash)}`;
  }

  _gerarStableId(especie = {}) {
    if (especie?.id !== null && especie?.id !== undefined && String(especie.id).trim() !== '') return `id:${String(especie.id).trim()}`;
    if (especie?.plataforma_id !== null && especie?.plataforma_id !== undefined && String(especie.plataforma_id).trim() !== '') return `pid:${String(especie.plataforma_id).trim()}`;
    const nomeCientifico = this._normalizarTextoSeguro(especie?.nome_cientifico || especie?.nome_cientifico_valido || '');
    if (nomeCientifico) return `nc:${this._hashDeterministico(nomeCientifico)}`;
    const nomePopular = this._normalizarTextoSeguro(especie?.nome_popular || '');
    if (nomePopular) return `np:${this._hashDeterministico(nomePopular)}`;
    return `payload:${this._hashDeterministico(JSON.stringify({
      sinonimos: especie?.sinonimos || [],
      nomes_populares: especie?.nomes_populares || [],
      fonte: especie?.fonte || especie?.origem || '',
    }))}`;
  }

  _normalizarEspecieReferencial(especie = {}) {
    const stable_id = this._gerarStableId(especie);
    const idPrincipal = especie.id ?? especie.plataforma_id ?? stable_id;
    return {
      id: idPrincipal,
      stable_id,
      plataforma_id: especie.plataforma_id ?? especie.id ?? null,
      nome_popular: especie.nome_popular || '',
      nome_cientifico: especie.nome_cientifico || '',
      sinonimos: especie.sinonimos || [],
      nomes_populares: especie.nomes_populares || [especie.nome_popular].filter(Boolean),
      parte_comestivel: especie.parte_comestivel || '',
      forma_uso: especie.forma_uso || '',
      epoca_frutificacao: especie.epoca_frutificacao || '',
      epoca_colheita: especie.epoca_colheita || '',
      bioma: especie.bioma || '',
      regiao_ocorrencia: especie.regiao_ocorrencia || '',
      origem: especie.origem || '',
      fonte: especie.fonte || '',
      ja_baixada: !!especie.ja_baixada,
      tamanho_estimado_mb: Number(especie.tamanho_estimado_mb || 0.5),
      tem_modelo_ar: !!especie.tem_modelo_ar,
      num_variacoes: Number(especie.num_variacoes || 0),
      grupo_taxonomico: especie.grupo_taxonomico || '',
      tipo: especie.tipo || 'referencial',
    };
  }

  _deduplicarEspecies(especies = []) {
    const mapa = new Map();
    for (const especie of especies) {
      const normalizada = this._normalizarEspecieReferencial(especie);
      const key = normalizada.nome_cientifico
        ? `nc:${this._normalizarTextoSeguro(normalizada.nome_cientifico)}`
        : (normalizada.plataforma_id ? `pid:${normalizada.plataforma_id}` : `sid:${normalizada.stable_id}`);
      mapa.set(key, normalizada);
    }
    return Array.from(mapa.values());
  }

  // ===================================
  // LISTAGEM E BUSCA
  // ===================================

  /**
   * Fluxo B (somente listagem/gerenciamento offline):
   * Lista plantas disponíveis para download, pacotes e manutenção.
   * NÃO deve ser usado como fonte da busca ativa referencial do campo de pesquisa.
   */
  async listarPlantasDisponiveis(filtros = {}) {
    const payloadFiltros = { ...filtros };
    delete payloadFiltros.busca;
    delete payloadFiltros.q;

    // Fluxo B: listagem de plantas/pacotes offline disponíveis (sem busca referencial)
    try {
      const params = new URLSearchParams(payloadFiltros).toString();
      const url = params
        ? `${API_ENDPOINTS.plantasOfflineDisponiveis}?${params}`
        : API_ENDPOINTS.plantasOfflineDisponiveis;

      const data = await httpGet(url);

      if (data?.sucesso) {
        const plantas = this._deduplicarEspecies(data.plantas || []);
        return {
          sucesso: true,
          plantas,
          total: plantas.length,
        };
      }

      return { sucesso: false, erro: data?.erro || 'Erro ao listar plantas' };
    } catch (error) {
      console.warn('Listagem online falhou, tentando offline:', error?.message || error);
      return { sucesso: false, erro: 'Erro ao listar plantas disponíveis', offline: true };
    }
  }

  /**
   * Busca espécies referenciais via endpoint canônico.
   * Pesquisa em: nome popular, científico, sinônimos, aliases, nomes populares,
   * família, gênero — com normalização de acentos e ranking por relevância.
   */
  async buscarEspeciesReferenciais(termo, filtros = {}) {
    // Fluxo B auxiliar: mantido para compatibilidade, mas a busca ativa da tela
    // Base Offline deve usar speciesFocusService.buscarEspeciesRecursivamente().
    const busca = String(termo || '').trim();
    if (busca.length < 2) {
      return { sucesso: true, plantas: [], total: 0, termo_buscado: busca };
    }

    const limite = filtros?.limite || 50;
    try {
      const url = `${API_ENDPOINTS.especiesReferenciaisBusca}?q=${encodeURIComponent(busca)}&limite=${limite}`;
      const data = await httpGet(url);

      if (data?.sucesso) {
        const plantas = this._deduplicarEspecies(data.especies || []);
        await this._atualizarCacheReferencial(plantas);
        return {
          sucesso: true,
          plantas,
          total: plantas.length,
          termo_buscado: data.termo_buscado || busca,
        };
      }
    } catch (error) {
      console.warn('Busca referencial online falhou, tentando cache offline:', error?.message || error);
    }

    return this._buscarBaseReferencialOffline(busca);
  }

  /**
   * Busca offline na base referencial já baixada.
   * Normaliza acentos e faz busca em nome popular, científico, sinônimos e aliases.
   */
  async _buscarBaseReferencialOffline(termo) {
    try {
      const cacheStr = await AsyncStorage.getItem(KEYS.BASE_REFERENCIAL_CACHE);
      if (!cacheStr) {
        // Tenta usar plantas já baixadas individualmente
        const baixadas = await this.listarPlantasBaixadas();
        if (baixadas.length === 0) {
          return { sucesso: false, erro: 'Sem dados offline disponíveis', offline: true };
        }
        const plantasOffline = [];
        for (const item of baixadas) {
          const dados = await this.buscarPlantaLocal(item.id);
          if (dados) plantasOffline.push(dados);
        }
        const filtradas = this._filtrarPlantasLocais(plantasOffline, termo);
        return { sucesso: true, plantas: filtradas, total: filtradas.length, offline: true };
      }

      const cache = JSON.parse(cacheStr);
      const todas = cache.especies || [];
      const filtradas = this._filtrarPlantasLocais(todas, termo);
      return { sucesso: true, plantas: filtradas, total: filtradas.length, offline: true };
    } catch (error) {
      console.warn('Erro ao buscar offline:', error?.message);
      return { sucesso: false, erro: 'Erro ao acessar dados offline', offline: true };
    }
  }

  /**
   * Filtra plantas locais com normalização de acentos e busca em múltiplos campos.
   */
  _filtrarPlantasLocais(plantas, termo) {
    if (!termo) return plantas;
    const termoNorm = this._normalizar(termo);

    const comScore = plantas
      .map(p => ({ planta: p, score: this._calcularRelevanciaLocal(p, termoNorm) }))
      .filter(item => item.score > 0);

    comScore.sort((a, b) => b.score - a.score);
    return comScore.map(item => item.planta);
  }

  _calcularRelevanciaLocal(planta, termoNorm) {
    let score = 0;
    const nomePopNorm = this._normalizar(planta.nome_popular || '');
    const nomeCientNorm = this._normalizar(planta.nome_cientifico || '');

    if (nomePopNorm === termoNorm) score += 100;
    else if (nomePopNorm.startsWith(termoNorm)) score += 50;
    else if (nomePopNorm.includes(termoNorm)) score += 20;

    if (nomeCientNorm === termoNorm) score += 95;
    else if (nomeCientNorm.startsWith(termoNorm)) score += 45;
    else if (nomeCientNorm.includes(termoNorm)) score += 18;

    for (const np of (planta.nomes_populares || [])) {
      const n = this._normalizar(np);
      if (n === termoNorm) { score += 80; break; }
      if (n.includes(termoNorm)) { score += 15; break; }
    }
    for (const alias of (planta.aliases || [])) {
      const a = this._normalizar(alias);
      if (a === termoNorm) { score += 70; break; }
      if (a.includes(termoNorm)) { score += 12; break; }
    }
    for (const sin of (planta.sinonimos || [])) {
      const s = this._normalizar(sin);
      if (s === termoNorm) { score += 60; break; }
      if (s.includes(termoNorm)) { score += 10; break; }
    }

    return score;
  }

  _normalizar(texto) {
    if (!texto) return '';
    return texto
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  /**
   * Atualiza o cache referencial local com os resultados do servidor.
   */
  async _atualizarCacheReferencial(especies) {
    try {
      const cacheStr = await AsyncStorage.getItem(KEYS.BASE_REFERENCIAL_CACHE);
      const cache = cacheStr ? JSON.parse(cacheStr) : { especies: [], atualizado_em: null };
      const mapa = new Map();
      for (const esp of (cache.especies || [])) {
        if (esp?.id) mapa.set(String(esp.id), this._normalizarEspecieReferencial(esp));
      }
      for (const esp of especies) {
        if (esp?.id) mapa.set(String(esp.id), this._normalizarEspecieReferencial(esp));
      }
      const novoCache = {
        especies: Array.from(mapa.values()),
        atualizado_em: new Date().toISOString(),
      };
      await AsyncStorage.setItem(KEYS.BASE_REFERENCIAL_CACHE, JSON.stringify(novoCache));
    } catch (error) {
      console.warn('Erro ao atualizar cache referencial:', error?.message);
    }
  }

  /**
   * Lista pacotes pré-definidos de plantas
   */
  async listarPacotes() {
    try {
      const cacheStr = await AsyncStorage.getItem(KEYS.PACOTES);
      if (cacheStr) {
        const cache = JSON.parse(cacheStr);
        if (Date.now() - cache.timestamp < 24 * 60 * 60 * 1000) {
          return { sucesso: true, pacotes: cache.data, fromCache: true };
        }
      }

      const data = await httpGet(API_ENDPOINTS.plantasOfflinePacotes);

      if (data?.sucesso) {
        await AsyncStorage.setItem(KEYS.PACOTES, JSON.stringify({
          data: data.pacotes,
          timestamp: Date.now(),
        }));
        return { sucesso: true, pacotes: data.pacotes };
      }

      return { sucesso: false, erro: data?.erro || 'Erro ao listar pacotes' };
    } catch (error) {
      console.warn('Erro ao listar pacotes:', error?.message || error);

      const cacheStr = await AsyncStorage.getItem(KEYS.PACOTES);
      if (cacheStr) {
        const cache = JSON.parse(cacheStr);
        return { sucesso: true, pacotes: cache.data, fromCache: true, offline: true };
      }

      return { sucesso: false, erro: error.message, offline: true };
    }
  }

  // ===================================
  // DOWNLOAD
  // ===================================

  /**
   * Baixa plantas selecionadas
   */
  async baixarPlantas(plantasIds, config = {}) {
    try {
      const data = await httpPost(API_ENDPOINTS.plantasOfflineBaixar, {
        plantas_ids: plantasIds,
        incluir_modelos_ar: config.incluir_modelos_ar || false,
        qualidade_fotos: config.qualidade_fotos || 'media',
        itens_selecionados: config.itens_selecionados || [],
      });

      if (data?.sucesso) {
        const promises = plantasIds.map(id =>
          this.baixarDadosPlanta(id, config.incluir_modelos_ar)
        );

        const resultados = [];
        for (let i = 0; i < promises.length; i += 3) {
          const batch = promises.slice(i, i + 3);
          const batchResults = await Promise.all(batch);
          resultados.push(...batchResults);
        }

        return {
          sucesso: true,
          plantasBaixadas: resultados.filter(r => r.sucesso).length,
          total: plantasIds.length,
        };
      }

      return { sucesso: false, erro: data?.erro || 'Erro ao iniciar download' };
    } catch (error) {
      console.error('Erro ao baixar plantas:', error?.message || error);
      return { sucesso: false, erro: error.message };
    }
  }

  /**
   * Baixa dados completos de uma planta específica
   */
  async baixarDadosPlanta(plantaId, incluirAR = false) {
    try {
      const params = incluirAR ? '?incluir_ar=true' : '';
      const url = `${API_ENDPOINTS.plantasOfflineDisponiveis.replace('/disponiveis/', '')}/${plantaId}/dados/${params}`;
      const data = await httpGet(url);

      if (data?.sucesso) {
        const dados = data.dados;
        await this.salvarPlantaLocal(plantaId, dados);
        return { sucesso: true, plantaId, tamanhoMb: dados.tamanho_total_mb };
      }

      return { sucesso: false, plantaId, erro: data?.erro };
    } catch (error) {
      console.error(`Erro ao baixar dados da planta ${plantaId}:`, error?.message || error);
      return { sucesso: false, plantaId, erro: error.message };
    }
  }

  /**
   * Baixa um pacote completo de plantas
   */
  async baixarPacote(pacoteId) {
    try {
      const url = `${API_ENDPOINTS.plantasOfflinePacotes}${pacoteId}/baixar/`;
      const data = await httpPost(url, {});

      if (data?.sucesso) {
        return {
          sucesso: true,
          mensagem: data.mensagem,
          totalPlantas: data.total_plantas,
        };
      }

      return { sucesso: false, erro: data?.erro };
    } catch (error) {
      console.error('Erro ao baixar pacote:', error?.message || error);
      return { sucesso: false, erro: error.message };
    }
  }

  // ===================================
  // ARMAZENAMENTO LOCAL
  // ===================================

  async salvarPlantaLocal(plantaId, dados) {
    const plantasBaixadas = await this.listarPlantasBaixadas();
    const index = plantasBaixadas.findIndex(p => p.id === plantaId);
    const plantaData = {
      id: plantaId,
      dados,
      baixadoEm: new Date().toISOString(),
      versao: dados.versao,
    };

    if (index >= 0) {
      plantasBaixadas[index] = plantaData;
    } else {
      plantasBaixadas.push(plantaData);
    }

    await AsyncStorage.setItem(KEYS.PLANTAS_BAIXADAS, JSON.stringify(plantasBaixadas));
    await AsyncStorage.setItem(`@planta_offline_${plantaId}`, JSON.stringify(dados));
  }

  async buscarPlantaLocal(plantaId) {
    try {
      const dadosStr = await AsyncStorage.getItem(`@planta_offline_${plantaId}`);
      return dadosStr ? JSON.parse(dadosStr) : null;
    } catch (error) {
      console.error('Erro ao buscar planta local:', error?.message);
      return null;
    }
  }

  async listarPlantasBaixadas() {
    try {
      const dadosStr = await AsyncStorage.getItem(KEYS.PLANTAS_BAIXADAS);
      return dadosStr ? JSON.parse(dadosStr) : [];
    } catch (error) {
      console.error('Erro ao listar plantas baixadas:', error?.message);
      return [];
    }
  }

  async removerPlantaLocal(plantaId) {
    await AsyncStorage.removeItem(`@planta_offline_${plantaId}`);
    const plantasBaixadas = await this.listarPlantasBaixadas();
    const novaLista = plantasBaixadas.filter(p => p.id !== plantaId);
    await AsyncStorage.setItem(KEYS.PLANTAS_BAIXADAS, JSON.stringify(novaLista));

    try {
      const url = `${API_ENDPOINTS.plantasOfflineDisponiveis.replace('/disponiveis/', '')}/${plantaId}/remover/`;
      await httpDelete(url);
    } catch (e) {
      console.warn('Erro ao notificar servidor sobre remoção (não crítico):', e?.message);
    }
  }

  async salvarPadroesIdentificacao() {
    const plantasBaixadas = await this.listarPlantasBaixadas();
    const padroes = [];

    for (const item of plantasBaixadas) {
      const dados = await this.buscarPlantaLocal(item.id);
      if (!dados) continue;

      const variacoes = Array.isArray(dados.variacoes) ? dados.variacoes : [];
      for (const variacao of variacoes) {
        if (!variacao?.features_ml || Object.keys(variacao.features_ml).length === 0) continue;
        padroes.push({
          planta_id: dados.id,
          nome_popular: dados.nome_popular,
          nome_cientifico: dados.nome_cientifico,
          variacao_id: variacao.id,
          nome_variacao: variacao.nome_variacao,
          features_ml: variacao.features_ml,
          origem: dados.fonte || 'integracao',
        });
      }
    }

    await AsyncStorage.setItem(KEYS.PADROES_IDENTIFICACAO, JSON.stringify({
      atualizado_em: new Date().toISOString(),
      total_padroes: padroes.length,
      itens: padroes,
    }));

    return padroes.length;
  }

  async sincronizarBaseIntegracao({ limite = 80 } = {}) {
    try {
      const metadata = await httpGet(API_ENDPOINTS.offlineBaseMetadata);
      const pacote = await httpGet(`${API_ENDPOINTS.offlineBaseDownload}?limite=${encodeURIComponent(limite)}`);
      const especies = Array.isArray(pacote?.especies) ? pacote.especies : [];
      if (!especies.length) {
        return { sucesso: false, erro: 'Nenhuma espécie recebida da base offline integrada.' };
      }

      for (const especie of especies) {
        await this.salvarPlantaLocal(especie.id, {
          id: especie.id,
          nome_popular: especie.nome_popular,
          nome_cientifico: especie.nome_cientifico,
          nome_cientifico_valido: especie.nome_cientifico_valido,
          parte_comestivel: especie.parte_comestivel,
          forma_uso: especie.forma_uso,
          epoca_frutificacao: especie.epoca_frutificacao,
          epoca_colheita: especie.epoca_colheita,
          grupo_taxonomico: especie.grupo_taxonomico,
          bioma: especie.bioma,
          regiao_ocorrencia: especie.regiao_ocorrencia,
          fonte: 'base_offline_integrada',
          versao: pacote?.metadata?.versao || metadata?.versao || String(Date.now()),
          variacoes: especie.variacoes || [],
          tamanho_total_mb: Number(especie?.tamanho_total_mb || 0.35),
        });
      }

      const totalPadroes = await this.salvarPadroesIdentificacao();
      await AsyncStorage.setItem(KEYS.ULTIMA_SYNC, new Date().toISOString());

      // Atualiza cache referencial com as espécies sincronizadas
      await this._atualizarCacheReferencial(especies);

      return {
        sucesso: especies.length > 0,
        plantasSincronizadas: especies.length,
        plantasSolicitadas: especies.length,
        totalPadroes,
        origem: 'bases_integradas_referenciais',
        versao: pacote?.metadata?.versao || metadata?.versao || '',
      };
    } catch (error) {
      console.warn('Erro ao sincronizar base de integração offline:', error?.message || error);
      return { sucesso: false, erro: error?.message || 'Falha ao sincronizar base integrada offline' };
    }
  }

  // ===================================
  // IDENTIFICAÇÃO OFFLINE
  // ===================================

  async identificarOffline(imageFeatures) {
    try {
      const plantasBaixadas = await this.listarPlantasBaixadas();
      if (plantasBaixadas.length === 0) {
        return { sucesso: false, erro: 'Nenhuma planta disponível offline' };
      }

      const resultados = [];

      for (const plantaBaixada of plantasBaixadas) {
        const dados = await this.buscarPlantaLocal(plantaBaixada.id);
        if (!dados) continue;

        let melhorScore = 0;
        let melhorMatch = null;

        if (dados.variacoes && dados.variacoes.length > 0) {
          for (const variacao of dados.variacoes) {
            if (variacao.features_ml) {
              const score = this.calcularSimilaridade(imageFeatures, variacao.features_ml);
              if (score > melhorScore) {
                melhorScore = score;
                melhorMatch = { ...dados, variacaoIdentificada: variacao };
              }
            }
          }
        }

        if (melhorScore > 0) {
          resultados.push({ planta: melhorMatch || dados, score: melhorScore });
        }
      }

      resultados.sort((a, b) => b.score - a.score);

      if (resultados.length > 0 && resultados[0].score > 0.5) {
        const melhor = resultados[0];
        return {
          sucesso: true,
          planta: melhor.planta,
          score: melhor.score,
          metodo: 'offline',
          alternativas: resultados.slice(1, 4),
        };
      }

      return {
        sucesso: false,
        erro: 'Nenhuma correspondência encontrada',
        resultados: resultados.slice(0, 5),
      };
    } catch (error) {
      console.error('Erro ao identificar offline:', error?.message || error);
      return { sucesso: false, erro: error.message };
    }
  }

  calcularSimilaridade(features1, features2) {
    if (!features1 || !features2) return 0;

    let score = 0;
    let count = 0;

    if (features1.hist_r && features2.hist_r) {
      score += this.compararHistogramas(features1.hist_r, features2.hist_r);
      count++;
    }
    if (features1.hist_g && features2.hist_g) {
      score += this.compararHistogramas(features1.hist_g, features2.hist_g);
      count++;
    }
    if (features1.hist_b && features2.hist_b) {
      score += this.compararHistogramas(features1.hist_b, features2.hist_b);
      count++;
    }
    if (features1.cor_media && features2.cor_media) {
      const diff = Math.abs(features1.cor_media - features2.cor_media);
      score += Math.max(0, 1 - diff / 255);
      count++;
    }
    if (features1.textura_std && features2.textura_std) {
      const diff = Math.abs(features1.textura_std - features2.textura_std);
      score += Math.max(0, 1 - diff / 100);
      count++;
    }

    return count > 0 ? score / count : 0;
  }

  compararHistogramas(hist1, hist2) {
    if (!Array.isArray(hist1) || !Array.isArray(hist2)) return 0;
    if (hist1.length !== hist2.length) return 0;

    let distance = 0;
    for (let i = 0; i < hist1.length; i++) {
      const sum = hist1[i] + hist2[i];
      if (sum > 0) {
        const diff = hist1[i] - hist2[i];
        distance += (diff * diff) / sum;
      }
    }

    return Math.max(0, 1 - distance / hist1.length);
  }

  // ===================================
  // CONFIGURAÇÕES
  // ===================================

  async obterConfiguracoes() {
    try {
      const cacheStr = await AsyncStorage.getItem(KEYS.CONFIG_OFFLINE);
      let configLocal = cacheStr ? JSON.parse(cacheStr) : null;

      const data = await httpGet(API_ENDPOINTS.plantasOfflineConfiguracoes);

      if (data?.sucesso) {
        await AsyncStorage.setItem(KEYS.CONFIG_OFFLINE, JSON.stringify(data.configuracoes));
        return { sucesso: true, configuracoes: data.configuracoes };
      }

      if (configLocal) {
        return { sucesso: true, configuracoes: configLocal, fromCache: true };
      }

      return { sucesso: false, erro: data?.erro };
    } catch (error) {
      console.warn('Erro ao obter configurações:', error?.message || error);

      const cacheStr = await AsyncStorage.getItem(KEYS.CONFIG_OFFLINE);
      if (cacheStr) {
        return { sucesso: true, configuracoes: JSON.parse(cacheStr), fromCache: true, offline: true };
      }

      return { sucesso: true, configuracoes: this.configPadrao(), default: true };
    }
  }

  async atualizarConfiguracoes(config) {
    try {
      const data = await httpPut(API_ENDPOINTS.plantasOfflineConfiguracoes, config);

      if (data?.sucesso) {
        await AsyncStorage.setItem(KEYS.CONFIG_OFFLINE, JSON.stringify(config));
        return { sucesso: true, mensagem: data.mensagem };
      }

      return { sucesso: false, erro: data?.erro };
    } catch (error) {
      console.warn('Erro ao atualizar configurações (salvo localmente):', error?.message);
      await AsyncStorage.setItem(KEYS.CONFIG_OFFLINE, JSON.stringify(config));
      return { sucesso: true, mensagem: 'Configurações salvas localmente', offline: true };
    }
  }

  configPadrao() {
    return {
      baixar_apenas_wifi: true,
      qualidade_fotos: 'media',
      incluir_modelos_ar: false,
      limite_armazenamento_mb: 500,
      auto_limpar_antigas: false,
      auto_atualizar: true,
      frequencia_atualizacao: 'semanal',
    };
  }

  // ===================================
  // ESTATÍSTICAS
  // ===================================

  async obterEstatisticas() {
    try {
      const plantasBaixadas = await this.listarPlantasBaixadas();

      let tamanhoTotal = 0;
      for (const planta of plantasBaixadas) {
        const dados = await this.buscarPlantaLocal(planta.id);
        if (dados && dados.tamanho_total_mb) {
          tamanhoTotal += dados.tamanho_total_mb;
        }
      }

      const config = await this.obterConfiguracoes();
      const limite = config.configuracoes?.limite_armazenamento_mb || 500;

      return {
        totalPlantas: plantasBaixadas.length,
        tamanhoTotalMb: Math.round(tamanhoTotal * 100) / 100,
        limiteMb: limite,
        percentualUsado: Math.round((tamanhoTotal / limite) * 100),
        ultimaSync: await AsyncStorage.getItem(KEYS.ULTIMA_SYNC),
      };
    } catch (error) {
      console.error('Erro ao obter estatísticas:', error?.message);
      return {
        totalPlantas: 0,
        tamanhoTotalMb: 0,
        limiteMb: 500,
        percentualUsado: 0,
      };
    }
  }

  async limparPlantasAntigas(diasSemUso = 30) {
    try {
      const plantasBaixadas = await this.listarPlantasBaixadas();
      const dataLimite = new Date();
      dataLimite.setDate(dataLimite.getDate() - diasSemUso);

      let removidas = 0;
      for (const planta of plantasBaixadas) {
        const dataBaixada = new Date(planta.baixadoEm);
        if (dataBaixada < dataLimite) {
          await this.removerPlantaLocal(planta.id);
          removidas++;
        }
      }

      return { sucesso: true, plantasRemovidas: removidas };
    } catch (error) {
      console.error('Erro ao limpar plantas antigas:', error?.message);
      return { sucesso: false, erro: error.message };
    }
  }
}

export default new PlantasOfflineService();
