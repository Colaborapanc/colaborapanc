/**
 * Configuração centralizada da API (fonte única de verdade para app mobile)
 */

import { Platform } from 'react-native';
import Constants from 'expo-constants';

const stripTrailingSlash = (value = '') => value.replace(/\/+$/, '');

const extractExpoHost = () => {
  const candidates = [
    Constants?.expoGoConfig?.debuggerHost,
    Constants?.manifest2?.extra?.expoGo?.debuggerHost,
    Constants?.manifest?.debuggerHost,
  ].filter(Boolean);

  const hostPort = candidates[0];
  if (!hostPort) return null;
  return hostPort.split(':')[0];
};

const resolveApiBaseUrl = () => {
  const envUrl = process.env.EXPO_PUBLIC_API_URL;
  const devFallback = 'http://localhost:8000';
  const raw = envUrl || (__DEV__ ? devFallback : '');
  if (!raw) {
    console.warn('[API] EXPO_PUBLIC_API_URL não definido em produção. Defina a variável de ambiente para evitar falhas.');
    return '';
  }
  const cleaned = stripTrailingSlash(raw);

  const isLocalhost = /localhost|127\.0\.0\.1/.test(cleaned);
  if (!isLocalhost) return cleaned;

  const runningOnDevice = Platform.OS === 'ios' || Platform.OS === 'android';
  if (!runningOnDevice) return cleaned;

  const expoHost = extractExpoHost();
  if (expoHost) {
    const fallback = `http://${expoHost}:8000`;
    console.log(`[API] EXPO_PUBLIC_API_URL usa localhost; fallback automático para ${fallback}`);
    return fallback;
  }

  return cleaned;
};

const API_BASE_URL = resolveApiBaseUrl();

export const API_URL = API_BASE_URL;

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
};

export const API_ENDPOINTS = {
  login: `${API_BASE_URL}/api/token/login/`,
  logout: `${API_BASE_URL}/api/logout/`,
  register: `${API_BASE_URL}/api/register/`,

  pontos: `${API_BASE_URL}/api/pontos/`,
  pontosProximos: `${API_BASE_URL}/api/rotas/pontos-proximos/`,
  cadastrarPonto: `${API_BASE_URL}/api/pontos/`,
  pontoDetalhe: (id) => `${API_BASE_URL}/api/pontos/${id}/`,
  pontoRevalidar: (id) => `${API_BASE_URL}/api/pontos/${id}/revalidar/`,
  pontoEnriquecimento: (id) => `${API_BASE_URL}/api/pontos/${id}/enriquecimento/`,
  pontosRevalidarLote: `${API_BASE_URL}/api/pontos/revalidar-lote/`,

  perfil: `${API_BASE_URL}/api/preferencias/`,
  userProfile: `${API_BASE_URL}/api/user/profile/`,
  changePassword: `${API_BASE_URL}/api/user/change-password/`,
  ranking: `${API_BASE_URL}/api/ranking/`,
  badges: `${API_BASE_URL}/api/badges/`,
  missoes: `${API_BASE_URL}/missoes/`,

  pontosRevisao: `${API_BASE_URL}/api/cientifico/revisao/fila/`,
  validarPonto: (id) => `${API_BASE_URL}/validar-ponto/${id}/`,

  pontosRevisaoCientifica: `${API_BASE_URL}/api/cientifico/revisao/fila/`,
  detalheRevisaoPonto: (id) => `${API_BASE_URL}/api/cientifico/revisao/pontos/${id}/`,
  validarPontoCientifico: (id) => `${API_BASE_URL}/api/cientifico/pontos/${id}/validacao/`,
  inferenciaPonto: (id) => `${API_BASE_URL}/api/cientifico/pontos/${id}/inferencia/`,
  dashboardCientifico: `${API_BASE_URL}/api/cientifico/dashboard/`,

  alertas: `${API_BASE_URL}/alertas/`,
  historicoAlertas: `${API_BASE_URL}/historico_alertas_api/`,

  identificarPlanta: `${API_BASE_URL}/identificar_planta/`,
  identificarPlantaAvancada: `${API_BASE_URL}/api/identificar-planta/`,
  identificarPlantaMobile: `${API_BASE_URL}/api/mobile/identificacao/imagem/`,
  buscarPlantas: `${API_BASE_URL}/api/buscar-plantas/`,
  pontosMapaPreview: `${API_BASE_URL}/api/mobile/mapa/previews/`,

  plantasCustomizadas: `${API_BASE_URL}/api/plantas-customizadas/`,
  validarPlantaCustomizada: (id) => `${API_BASE_URL}/api/plantas-customizadas/${id}/validar/`,
  extrairFeaturesPlanta: (id) => `${API_BASE_URL}/api/plantas-customizadas/${id}/extrair_features/`,

  modelosAR: `${API_BASE_URL}/api/modelos-ar/`,
  modelosARDisponiveis: `${API_BASE_URL}/api/modelos-ar-disponiveis/`,
  previewModeloAR: (id) => `${API_BASE_URL}/api/modelos-ar/${id}/preview/`,

  historicoIdentificacao: `${API_BASE_URL}/api/historico-identificacao/`,
  estatisticasIdentificacao: `${API_BASE_URL}/api/historico-identificacao/estatisticas/`,

  offlineSync: `${API_BASE_URL}/api/offline-sync/`,
  pushToken: `${API_BASE_URL}/api/push-token/`,
  notificacoes: `${API_BASE_URL}/api/notificacoes/`,
  conversas: `${API_BASE_URL}/api/conversas/`,
  mensagens: `${API_BASE_URL}/api/mensagens/`,
  compartilhamentos: `${API_BASE_URL}/api/compartilhamentos/`,

  recomendacoes: `${API_BASE_URL}/api/recomendacoes/`,
  integracoesEcommerce: `${API_BASE_URL}/api/integracoes-ecommerce/`,
  produtosSemente: `${API_BASE_URL}/api/produtos-semente/`,
  roteiros: `${API_BASE_URL}/api/roteiros/`,
  referenciasAr: `${API_BASE_URL}/api/referencias-ar/`,

  // Endpoint canônico da busca digitada na Base Offline de Espécies.
  especiesReferenciaisBusca: `${API_BASE_URL}/api/especies-referenciais/busca/`,
  especiesReferenciaisBuscaRecursiva: `${API_BASE_URL}/api/especies-referenciais/busca-recursiva/`,
  // Aceita download_id interno (numérico) e externo/canônico (string).
  plantasOfflineDisponiveis: `${API_BASE_URL}/api/plantas-offline/disponiveis/`,
  plantasOfflinePacotes: `${API_BASE_URL}/api/plantas-offline/pacotes/`,
  plantasOfflineBaixar: `${API_BASE_URL}/api/plantas-offline/baixar/`,
  plantasOfflineMinhas: `${API_BASE_URL}/api/plantas-offline/minhas/`,
  plantasOfflineConfiguracoes: `${API_BASE_URL}/api/plantas-offline/configuracoes/`,
  offlineBaseMetadata: `${API_BASE_URL}/api/mobile/offline/base/metadata/`,
  offlineBaseDownload: `${API_BASE_URL}/api/mobile/offline/base/`,

  // Enriquecimento taxonômico
  enriquecimento: `${API_BASE_URL}/api/enriquecimento/`,
  enriquecimentoRevalidar: `${API_BASE_URL}/api/enriquecimento/revalidar/`,
  enriquecimentoPlanta: (id) => `${API_BASE_URL}/api/enriquecimento/${id}/`,
  enriquecimentoHistorico: (id) => `${API_BASE_URL}/api/enriquecimento/${id}/historico/`,
};

export const buildURL = (path) => {
  if (path.startsWith('http')) return path;
  if (!API_BASE_URL) {
    throw new Error('API base URL não configurada. Defina EXPO_PUBLIC_API_URL.');
  }
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
};

export default API_CONFIG;
