/**
 * Serviço de Identificação de Plantas
 *
 * Integra com o sistema avançado de identificação que usa:
 * - Base de dados customizada
 * - Google Cloud Vision
 * - PlantNet
 * - Plant.id
 *
 * Usa httpClient centralizado para auth, headers e timeout.
 */

import { API_ENDPOINTS } from '../config/api';
import plantasOfflineService from './plantasOfflineService';
import NetInfo from '@react-native-community/netinfo';
import { httpGet, httpPost } from './httpClient';

const readImageAsBase64 = async (imageUri) => {
  // Try the new File API first (SDK 54+)
  try {
    const { File } = await import('expo-file-system/next');
    const file = new File(imageUri);
    if (file.exists) {
      return await file.base64();
    }
  } catch (_ignored) {
    // new API not available
  }

  // Fallback to legacy readAsStringAsync
  try {
    const FileSystem = require('expo-file-system');
    const readFn = FileSystem?.readAsStringAsync || FileSystem?.default?.readAsStringAsync;
    if (typeof readFn === 'function') {
      return readFn(imageUri, { encoding: 'base64' });
    }
  } catch (_ignored) {
    // not available
  }

  throw new Error('Nenhuma API de leitura de arquivos disponível no expo-file-system');
};

/**
 * Decodifica base64 para array de bytes
 */
const base64ToBytes = (base64) => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  const lookup = new Uint8Array(128);
  for (let i = 0; i < chars.length; i++) lookup[chars.charCodeAt(i)] = i;

  const len = base64.length;
  let bufLen = (len * 3) >> 2;
  if (base64[len - 1] === '=') bufLen--;
  if (base64[len - 2] === '=') bufLen--;

  const bytes = new Uint8Array(bufLen);
  let p = 0;
  for (let i = 0; i < len; i += 4) {
    const a = lookup[base64.charCodeAt(i)];
    const b = lookup[base64.charCodeAt(i + 1)];
    const c = lookup[base64.charCodeAt(i + 2)];
    const d = lookup[base64.charCodeAt(i + 3)];
    bytes[p++] = (a << 2) | (b >> 4);
    if (p < bufLen) bytes[p++] = ((b & 15) << 4) | (c >> 2);
    if (p < bufLen) bytes[p++] = ((c & 3) << 6) | d;
  }
  return bytes;
};

const extrairFeaturesImagem = async (imageUri) => {
  try {
    const base64 = await readImageAsBase64(imageUri);
    if (!base64) return null;

    const bytes = base64ToBytes(base64);
    const totalBytes = bytes.length;
    if (totalBytes < 100) return null;

    const startOffset = Math.min(100, Math.floor(totalBytes * 0.05));
    const sampleSize = Math.min(totalBytes - startOffset, 30000);
    const step = Math.max(3, Math.floor(sampleSize / 3000) * 3);

    const hist_r = Array(32).fill(0);
    const hist_g = Array(32).fill(0);
    const hist_b = Array(32).fill(0);

    let soma = 0;
    let somaQuadrados = 0;
    let total = 0;

    for (let i = startOffset; i + 2 < startOffset + sampleSize; i += step) {
      const r = bytes[i];
      const g = bytes[i + 1];
      const b = bytes[i + 2];
      hist_r[Math.min(31, r >> 3)] += 1;
      hist_g[Math.min(31, g >> 3)] += 1;
      hist_b[Math.min(31, b >> 3)] += 1;
      const luma = 0.299 * r + 0.587 * g + 0.114 * b;
      soma += luma;
      somaQuadrados += luma * luma;
      total += 1;
    }

    const normalizar = (arr) => {
      if (!total) return arr;
      return arr.map((v) => v / total);
    };

    const corMedia = total ? soma / total : 0;
    const variancia = total ? Math.max(0, somaQuadrados / total - corMedia * corMedia) : 0;

    return {
      hist_r: normalizar(hist_r),
      hist_g: normalizar(hist_g),
      hist_b: normalizar(hist_b),
      cor_media: corMedia,
      textura_std: Math.sqrt(variancia),
    };
  } catch (error) {
    console.error('Erro ao extrair features:', error?.message || error);
    return null;
  }
};

/**
 * Identifica uma planta usando apenas dados offline
 */
export const identificarPlantaOffline = async (imageUri) => {
  try {
    let plantasBaixadas = await plantasOfflineService.listarPlantasBaixadas();

    if (plantasBaixadas.length === 0) {
      const syncIntegracao = await plantasOfflineService.sincronizarBaseIntegracao();
      if (syncIntegracao?.sucesso) {
        plantasBaixadas = await plantasOfflineService.listarPlantasBaixadas();
      }
      if (plantasBaixadas.length === 0) {
        return {
          sucesso: false,
          erro: 'Nenhuma planta disponível offline. Por favor, baixe plantas primeiro.',
          semPlantasOffline: true,
        };
      }
    }

    const features = await extrairFeaturesImagem(imageUri);
    if (!features) {
      return { sucesso: false, erro: 'Erro ao processar imagem' };
    }

    const resultado = await plantasOfflineService.identificarOffline(features);

    if (resultado.sucesso) {
      const p = resultado.planta;
      return {
        sucesso: true,
        dados: {
          sucesso: true,
          metodo: 'offline',
          nome_popular: p.nome_popular,
          nome_cientifico: p.nome_cientifico,
          score: resultado.score,
          tempo_processamento: 0,
          planta_base_id: p.id,
          descricao: p.forma_uso || '',
          parte_comestivel: p.parte_comestivel || '',
          forma_uso: p.forma_uso || '',
          epoca_frutificacao: p.epoca_frutificacao || '',
          epoca_colheita: p.epoca_colheita || '',
          grupo_taxonomico: p.grupo_taxonomico || '',
          bioma: p.bioma || '',
          offline: true,
          alternativas: resultado.alternativas || [],
        },
      };
    }

    return {
      sucesso: false,
      erro: resultado.erro || 'Nenhuma correspondência encontrada',
      resultados: resultado.resultados || [],
    };
  } catch (error) {
    console.error('Erro na identificação offline:', error?.message || error);
    return { sucesso: false, erro: error.message || 'Erro ao identificar offline' };
  }
};

/**
 * Identifica uma planta a partir de uma imagem.
 * Regra: online primeiro quando há conectividade; offline apenas sem conectividade.
 */
export const identificarPlanta = async (imageUri, options = {}) => {
  try {
    const {
      usarCustomDB = true,
      usarGoogle = true,
      salvarHistorico = true,
      pontoId = null,
      forcarOnline = false,
      tentarOfflinePrimeiro = false,
    } = options;

    const netInfo = await NetInfo.fetch();
    const temConexao = !!(netInfo.isConnected && netInfo.isInternetReachable !== false);

    // Sem internet: usar fallback offline explícito
    if (!temConexao) {
      const resultadoOffline = await identificarPlantaOffline(imageUri);

      if (resultadoOffline.sucesso && resultadoOffline.dados.score >= 0.6) {
        return {
          ...resultadoOffline,
          avisoFallback: 'Sem conectividade. Resultado obtido pela base offline local.',
        };
      }

      return resultadoOffline.semPlantasOffline ? resultadoOffline : {
        sucesso: false,
        erro: 'Sem conexão e nenhuma planta identificada offline. Baixe a base offline integrada.',
        resultadoOffline,
      };
    }

    // Com internet: sempre priorizar integrações online
    const formData = new FormData();

      const filename = imageUri.split('/').pop();
      const match = /\.(\w+)$/.exec(filename);
      const type = match ? `image/${match[1]}` : 'image/jpeg';

      formData.append('imagem', { uri: imageUri, name: filename, type });
      formData.append('usar_custom_db', String(usarCustomDB));
      formData.append('usar_google', String(usarGoogle));
      formData.append('salvar_historico', String(salvarHistorico));

      if (pontoId) {
        formData.append('ponto_id', String(pontoId));
      }

    const data = await httpPost(API_ENDPOINTS.identificarPlantaMobile, formData);
    const score = Number(data?.score || 0);

    if (score >= 0.5 || forcarOnline) {
      return {
        sucesso: true,
        dados: { ...data, offline: false, origem_dados: 'integracoes_online' },
      };
    }

    // Apoio local quando integração online retorna baixa confiança
    const apoioLocal = await identificarPlantaOffline(imageUri);
    if (apoioLocal.sucesso) {
      return {
        ...apoioLocal,
        avisoFallback: 'Integração online inconclusiva. Resultado sugerido pela base integrada local.',
        dados: {
          ...(apoioLocal.dados || {}),
          metodo: 'base_integrada_local_apoio',
          offline: false,
          origem_dados: 'cache_integrado_local',
        },
      };
    }

    return {
      sucesso: true,
      dados: { ...data, offline: false, origem_dados: 'integracoes_online' },
    };
  } catch (error) {
    console.error('Erro ao identificar planta:', error?.message || error);

    // Fallback offline em caso de erro online
    if (!options.forcarOnline) {
      const resultadoOffline = await identificarPlantaOffline(imageUri);
      if (resultadoOffline.sucesso) {
        return {
          ...resultadoOffline,
          avisoFallback: 'Identificação realizada offline devido a erro na conexão',
        };
      }
    }

    const erroRede = error?.code === 'NETWORK' || error?.code === 'TIMEOUT';
    return {
      sucesso: false,
      erro: erroRede
        ? 'Falha de rede ao acessar serviço de identificação online.'
        : (error?.message || 'Erro desconhecido'),
    };
  }
};

/**
 * Busca plantas offline por nome (nas plantas baixadas)
 */
const buscarPlantasOffline = async (termo) => {
  try {
    const plantasBaixadas = await plantasOfflineService.listarPlantasBaixadas();
    if (!plantasBaixadas || plantasBaixadas.length === 0) return [];

    const termoLower = termo.toLowerCase();
    return plantasBaixadas
      .filter((p) => {
        const nomePopular = (p.nome_popular || '').toLowerCase();
        const nomeCientifico = (p.nome_cientifico || '').toLowerCase();
        return nomePopular.includes(termoLower) || nomeCientifico.includes(termoLower);
      })
      .slice(0, 10)
      .map((p) => ({
        id: p.id,
        nome_popular: p.nome_popular,
        nome_cientifico: p.nome_cientifico,
        parte_comestivel: p.parte_comestivel || '',
        forma_uso: p.forma_uso || '',
        epoca_frutificacao: p.epoca_frutificacao || '',
        epoca_colheita: p.epoca_colheita || '',
        grupo_taxonomico: p.grupo_taxonomico || '',
        bioma: p.bioma || '',
        fonte: 'offline',
      }));
  } catch (error) {
    console.warn('Busca offline falhou:', error?.message);
    return [];
  }
};

/**
 * Busca plantas por nome (online + offline merge)
 */
export const buscarPlantas = async (termo) => {
  try {
    if (!termo || termo.length < 2) {
      return { sucesso: false, erro: 'Termo de busca deve ter pelo menos 2 caracteres' };
    }

    const netInfo = await NetInfo.fetch();
    const temConexao = !!(netInfo.isConnected && netInfo.isInternetReachable !== false);

    let resultadosOnline = [];

    if (temConexao) {
      try {
        const data = await httpGet(`${API_ENDPOINTS.buscarPlantas}?q=${encodeURIComponent(termo)}`);
        resultadosOnline = data?.resultados || data?.plantas || data?.plantas_referenciais || (Array.isArray(data) ? data : []);
      } catch (error) {
        console.warn('Busca online falhou, usando offline:', error?.message);
      }
    }

    const resultadosOffline = await buscarPlantasOffline(termo);

    // Merge: online primeiro, offline depois, sem duplicatas
    const idsVistos = new Set();
    const resultadosMerge = [];

    for (const item of [...resultadosOnline, ...resultadosOffline]) {
      const id = item.id || item.planta_id;
      if (id && idsVistos.has(id)) continue;
      if (id) idsVistos.add(id);
      resultadosMerge.push(item);
    }

    return { sucesso: true, dados: resultadosMerge };
  } catch (error) {
    console.error('Erro ao buscar plantas:', error?.message || error);

    const resultadosOffline = await buscarPlantasOffline(termo);
    if (resultadosOffline.length > 0) {
      return { sucesso: true, dados: resultadosOffline };
    }

    return { sucesso: false, erro: error?.message || 'Erro ao buscar plantas' };
  }
};

/**
 * Obtém modelos AR disponíveis
 */
export const obterModelosAR = async (plantaId = null) => {
  try {
    const url = plantaId
      ? `${API_ENDPOINTS.modelosARDisponiveis}?planta=${plantaId}`
      : API_ENDPOINTS.modelosARDisponiveis;
    const data = await httpGet(url);
    return { sucesso: true, modelos: data?.modelos || [] };
  } catch (error) {
    console.error('Erro ao obter modelos AR:', error?.message || error);
    return { sucesso: false, erro: error.message || 'Erro ao carregar modelos AR', modelos: [] };
  }
};

/**
 * Obtém histórico de identificações do usuário
 */
export const obterHistoricoIdentificacao = async (filtros = {}) => {
  try {
    const params = new URLSearchParams(filtros).toString();
    const url = params
      ? `${API_ENDPOINTS.historicoIdentificacao}?${params}`
      : API_ENDPOINTS.historicoIdentificacao;
    const data = await httpGet(url);
    return { sucesso: true, historico: data?.results || data };
  } catch (error) {
    console.error('Erro ao obter histórico:', error?.message || error);
    return { sucesso: false, erro: error.message || 'Erro ao carregar histórico', historico: [] };
  }
};

/**
 * Obtém estatísticas de identificação do usuário
 */
export const obterEstatisticasIdentificacao = async () => {
  try {
    const data = await httpGet(API_ENDPOINTS.estatisticasIdentificacao);
    return { sucesso: true, estatisticas: data };
  } catch (error) {
    console.error('Erro ao obter estatísticas:', error?.message || error);
    return { sucesso: false, erro: error.message || 'Erro ao carregar estatísticas', estatisticas: null };
  }
};

/**
 * Cadastra uma planta customizada
 */
export const cadastrarPlantaCustomizada = async (dadosPlanta) => {
  try {
    const formData = new FormData();

    Object.keys(dadosPlanta).forEach(key => {
      if (key.startsWith('foto_') && dadosPlanta[key]) {
        const filename = dadosPlanta[key].split('/').pop();
        const match = /\.(\w+)$/.exec(filename);
        const type = match ? `image/${match[1]}` : 'image/jpeg';
        formData.append(key, { uri: dadosPlanta[key], name: filename, type });
      } else if (dadosPlanta[key] !== null && dadosPlanta[key] !== undefined) {
        formData.append(key, dadosPlanta[key]);
      }
    });

    const data = await httpPost(API_ENDPOINTS.plantasCustomizadas, formData);
    return { sucesso: true, planta: data };
  } catch (error) {
    console.error('Erro ao cadastrar planta customizada:', error?.message || error);
    return { sucesso: false, erro: error?.message || 'Erro ao cadastrar planta' };
  }
};

/**
 * Helper para formatar resultado de identificação para exibição
 */
export const formatarResultadoIdentificacao = (resultado) => {
  if (!resultado || !resultado.dados) return null;

  const { dados } = resultado;

  return {
    identificado: dados.sucesso,
    nomePopular: dados.nome_popular || 'Nome não identificado',
    nomeCientifico: dados.nome_cientifico || '',
    confianca: Math.round(dados.score * 100),
    metodo: dados.metodo,
    metodoNome: getMetodoNome(dados.metodo),
    tempoProcessamento: dados.tempo_processamento?.toFixed(2) || '0',
    plantaId: dados.planta_base_id,
    plantaCustomizadaId: dados.planta_customizada_id,
    descricao: dados.descricao || '',
    erro: dados.erro || '',
  };
};

const getMetodoNome = (metodo) => {
  const metodos = {
    'custom_ml': 'Base Customizada',
    'google_vision': 'Google Vision',
    'plantnet': 'PlantNet',
    'plantid': 'Plant.id',
    'manual': 'Manual',
    'nenhum': 'Não identificado',
  };
  return metodos[metodo] || metodo;
};

export const isResultadoConfiavel = (resultado) => {
  if (!resultado || !resultado.dados) return false;
  return resultado.dados.sucesso && resultado.dados.score >= 0.6;
};

export default {
  identificarPlanta,
  identificarPlantaOffline,
  buscarPlantas,
  obterModelosAR,
  obterHistoricoIdentificacao,
  obterEstatisticasIdentificacao,
  cadastrarPlantaCustomizada,
  formatarResultadoIdentificacao,
  isResultadoConfiavel,
};
