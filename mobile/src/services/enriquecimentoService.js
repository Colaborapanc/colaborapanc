/**
 * Serviço de enriquecimento taxonômico para o mobile.
 *
 * Todas as chamadas passam pelo backend - nunca chamamos APIs externas
 * diretamente para não expor chaves de API.
 */

import { API_ENDPOINTS } from '../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { httpGet, httpPost } from './httpClient';

const CACHE_KEY_PREFIX = 'enrichment_';
const CACHE_TTL_MS = 6 * 60 * 60 * 1000; // 6 horas

/**
 * Busca o token de autenticação do usuário.
 */
/**
 * Enriquece um nome científico via backend.
 * @param {string} nomeCientifico
 * @param {number|null} plantaId - ID da PlantaReferencial (opcional)
 * @returns {Promise<{sucesso: boolean, dados: object, erro: string|null}>}
 */
export async function enriquecerNome(nomeCientifico, plantaId = null) {
  if (!nomeCientifico || nomeCientifico.trim().length < 3) {
    return { sucesso: false, dados: null, erro: 'Nome científico muito curto' };
  }

  // Verificar cache local
  const cacheKey = `${CACHE_KEY_PREFIX}${nomeCientifico.toLowerCase().trim()}`;
  try {
    const cached = await AsyncStorage.getItem(cacheKey);
    if (cached) {
      const parsed = JSON.parse(cached);
      if (parsed.timestamp && Date.now() - parsed.timestamp < CACHE_TTL_MS) {
        return { sucesso: true, dados: parsed.dados, erro: null, fromCache: true };
      }
    }
  } catch (_) {
    // Cache miss, continuar
  }

  try {
    const body = { nome_cientifico: nomeCientifico.trim() };
    if (plantaId) {
      body.planta_id = plantaId;
    }

    const dados = await httpPost(API_ENDPOINTS.enriquecimento, body);

    // Salvar no cache local
    try {
      await AsyncStorage.setItem(cacheKey, JSON.stringify({
        dados,
        timestamp: Date.now(),
      }));
    } catch (_) {
      // Falha de cache não é crítica
    }

    return {
      sucesso: dados.status !== 'erro',
      dados,
      erro: dados.erros && dados.erros.length > 0 ? dados.erros.join('; ') : null,
    };
  } catch (error) {
    return {
      sucesso: false,
      dados: null,
      erro: `Erro de rede: ${error.message}`,
    };
  }
}

/**
 * Revalida uma planta existente.
 * @param {number} plantaId
 * @returns {Promise<{sucesso: boolean, dados: object, erro: string|null}>}
 */
export async function revalidarPlanta(plantaId) {
  if (!plantaId) {
    return { sucesso: false, dados: null, erro: 'planta_id obrigatório' };
  }

  try {
    const dados = await httpPost(API_ENDPOINTS.enriquecimentoRevalidar, { planta_id: plantaId });
    return {
      sucesso: dados.status !== 'erro',
      dados,
      erro: null,
    };
  } catch (error) {
    return {
      sucesso: false,
      dados: null,
      erro: `Erro de rede: ${error.message}`,
    };
  }
}

/**
 * Consulta o enriquecimento atual de uma planta.
 * @param {number} plantaId
 * @returns {Promise<{sucesso: boolean, dados: object, erro: string|null}>}
 */
export async function consultarEnriquecimento(plantaId) {
  if (!plantaId) {
    return { sucesso: false, dados: null, erro: 'planta_id obrigatório' };
  }

  try {
    const dados = await httpGet(API_ENDPOINTS.enriquecimentoPlanta(plantaId));
    return { sucesso: true, dados, erro: null };
  } catch (error) {
    return {
      sucesso: false,
      dados: null,
      erro: `Erro de rede: ${error.message}`,
    };
  }
}

/**
 * Busca histórico de enriquecimentos de uma planta.
 * @param {number} plantaId
 * @returns {Promise<{sucesso: boolean, historico: array, erro: string|null}>}
 */
export async function historicoEnriquecimento(plantaId) {
  if (!plantaId) {
    return { sucesso: false, historico: [], erro: 'planta_id obrigatório' };
  }

  try {
    const dados = await httpGet(API_ENDPOINTS.enriquecimentoHistorico(plantaId));
    return { sucesso: true, historico: dados, erro: null };
  } catch (error) {
    return {
      sucesso: false,
      historico: [],
      erro: `Erro de rede: ${error.message}`,
    };
  }
}

/**
 * Determina o selo de validação a partir dos dados de enriquecimento.
 * @param {object} enriquecimento - dados retornados por consultarEnriquecimento
 * @returns {'validado'|'parcialmente_validado'|'pendente'}
 */
export function calcularSeloValidacao(enriquecimento) {
  if (!enriquecimento) return 'pendente';
  const status = enriquecimento.status_enriquecimento || 'pendente';
  const grau = enriquecimento.grau_confianca;
  if (status === 'completo' && grau && grau >= 0.7) return 'validado';
  if ((status === 'parcial' || status === 'completo') && grau && grau >= 0.3) return 'parcialmente_validado';
  return 'pendente';
}

/**
 * Configuração do selo para exibição na UI.
 */
export const SELO_CONFIG = {
  validado: {
    label: 'Validado',
    color: '#16A34A',
    bgColor: '#DCFCE7',
    icon: 'checkmark-circle',
  },
  parcialmente_validado: {
    label: 'Parcialmente Validado',
    color: '#CA8A04',
    bgColor: '#FEF9C3',
    icon: 'alert-circle',
  },
  pendente: {
    label: 'Pendente',
    color: '#6B7280',
    bgColor: '#F3F4F6',
    icon: 'time-outline',
  },
};

export default {
  enriquecerNome,
  revalidarPlanta,
  consultarEnriquecimento,
  historicoEnriquecimento,
  calcularSeloValidacao,
  SELO_CONFIG,
};
