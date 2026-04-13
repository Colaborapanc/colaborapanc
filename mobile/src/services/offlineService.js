import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_ENDPOINTS } from '../config/api';
import { getAuthToken, httpGet, httpPost, setAuthToken } from './httpClient';
import {
  OFFLINE_KEYS,
  adicionarSyncQueue,
  atualizarSyncQueue,
  carregarPontosCache,
  listarPontosPendentes,
  limparPontosPendentes,
  listarSyncQueue,
  registrarSyncLog,
  removerPontoPendente,
  salvarPontoPendente,
  salvarPontosCache,
  salvarUltimaSync,
  obterUltimaSync,
} from './offlineStorage';

const MAX_RETRY = 5;

/**
 * Copia foto para diretório persistente do app para que não se perca
 * quando o SO limpar o cache de imagens temporárias.
 */
const persistirFotoLocal = async (fotoUri) => {
  if (!fotoUri || typeof fotoUri !== 'string') return fotoUri;
  try {
    const FileSystem = require('expo-file-system');
    const fs = FileSystem.default || FileSystem;
    if (!fs?.documentDirectory || !fs?.copyAsync) return fotoUri;

    // Se já está no documentDirectory, não precisa copiar
    if (fotoUri.startsWith(fs.documentDirectory)) return fotoUri;

    const filename = `offline_foto_${Date.now()}_${fotoUri.split('/').pop() || 'photo.jpg'}`;
    const destino = `${fs.documentDirectory}${filename}`;
    await fs.copyAsync({ from: fotoUri, to: destino });
    return destino;
  } catch (error) {
    console.warn('[offlineService] Não foi possível persistir foto localmente:', error?.message);
    return fotoUri; // Retorna original como fallback
  }
};

class OfflineService {
  constructor() {
    this.syncInProgress = false;
    this.lastSyncAttemptAt = 0;
    this.syncIntervalId = null;
    this.netInfoUnsubscribe = null;
    this.unauthorizedHandler = null;
  }

  setUnauthorizedHandler(handler) {
    this.unauthorizedHandler = typeof handler === 'function' ? handler : null;
  }

  async lidarComNaoAutorizado(error) {
    if (error?.status !== 401) return false;

    await registrarSyncLog({ nivel: 'warn', evento: 'sync_nao_autorizado', erro: error.message || '401 Unauthorized' });
    await setAuthToken(null);
    await AsyncStorage.multiRemove([
      'userId',
      OFFLINE_KEYS.PONTOS_PENDING,
      OFFLINE_KEYS.SYNC_QUEUE,
      OFFLINE_KEYS.SYNC_LOG,
      OFFLINE_KEYS.LAST_SYNC,
    ]);
    if (this.unauthorizedHandler) {
      await this.unauthorizedHandler();
    }
    return true;
  }

  async verificarConexao() {
    const state = await NetInfo.fetch();
    return !!(state.isConnected && state.isInternetReachable !== false);
  }

  async buscarPontos({ forcarOnline = false, usarPreviewMapa = false } = {}) {
    const online = await this.verificarConexao();

    if (online || forcarOnline) {
      try {
        const endpoint = usarPreviewMapa ? API_ENDPOINTS.pontosMapaPreview : API_ENDPOINTS.pontos;
        const payload = await httpGet(endpoint);
        const pontos = usarPreviewMapa ? (payload?.resultados || []) : payload;
        await salvarPontosCache(pontos);
        return { dados: pontos, fonte: 'online' };
      } catch (error) {
        await registrarSyncLog({ nivel: 'warn', evento: 'fetch_pontos_fallback_cache', erro: error.message });
      }
    }

    const cache = await carregarPontosCache();
    return { dados: cache, fonte: 'cache' };
  }

  buildPontoPayload(payload = {}) {
    const hasPhoto = typeof payload?.foto_uri === 'string' && payload.foto_uri.length > 0;
    if (!hasPhoto) return payload;

    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value === undefined || value === null) return;
      if (key === 'foto_uri') return;
      if (key === 'localizacao') {
        const coords = Array.isArray(value)
          ? value
          : (value?.coordinates || [value?.longitude, value?.latitude]);
        if (Array.isArray(coords) && coords.length === 2) {
          formData.append('localizacao', JSON.stringify([Number(coords[0]), Number(coords[1])]));
          formData.append('longitude', String(Number(coords[0])));
          formData.append('latitude', String(Number(coords[1])));
        } else {
          formData.append('localizacao', typeof value === 'string' ? value : JSON.stringify(value));
        }
        return;
      }
      formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
    });

    const filename = payload.foto_uri.split('/').pop() || `ponto_${Date.now()}.jpg`;
    const ext = filename.split('.').pop()?.toLowerCase();
    const mimeType = ext === 'png' ? 'image/png' : 'image/jpeg';
    formData.append('foto', { uri: payload.foto_uri, name: filename, type: mimeType });
    return formData;
  }

  async registrarPonto(payload) {
    const online = await this.verificarConexao();
    if (online) {
      try {
        const created = await httpPost(API_ENDPOINTS.pontos, this.buildPontoPayload(payload));
        const cache = await carregarPontosCache();
        await salvarPontosCache([created, ...cache]);
        return { sucesso: true, origem: 'online', item: created };
      } catch (error) {
        if (await this.lidarComNaoAutorizado(error)) {
          return { sucesso: false, origem: 'online', message: 'Sessão expirada. Faça login novamente.' };
        }
        await registrarSyncLog({ nivel: 'warn', evento: 'post_online_falhou_queue', erro: error.message });
      }
    }

    // Persistir foto em diretório permanente para não perder no sync posterior
    const payloadPersistido = { ...payload };
    if (payload.foto_uri) {
      payloadPersistido.foto_uri = await persistirFotoLocal(payload.foto_uri);
    }

    const pendente = await salvarPontoPendente(payloadPersistido);
    await adicionarSyncQueue({
      tipo: 'ponto_criar',
      idempotencyKey: pendente.id_temporario,
      endpoint: API_ENDPOINTS.pontos,
      payload: pendente,
    });

    return { sucesso: true, origem: 'offline', item: pendente };
  }

  async sincronizar() {
    const now = Date.now();
    if (this.syncInProgress || now - this.lastSyncAttemptAt < 8000) {
      return { success: false, message: 'Sincronização já em andamento' };
    }

    this.syncInProgress = true;
    this.lastSyncAttemptAt = now;

    try {
      const token = await getAuthToken();
      if (!token) {
        return { success: false, message: 'Usuário não autenticado' };
      }

      const online = await this.verificarConexao();
      if (!online) return { success: false, message: 'Sem conexão' };

      const queue = await listarSyncQueue();
      const remaining = [];
      let sincronizadas = 0;

      for (const item of queue) {
        try {
          if (item.tipo === 'ponto_criar') {
            const payload = this.buildPontoPayload(item.payload);
            const created = await httpPost(item.endpoint, payload);
            const cache = await carregarPontosCache();
            const semTemporario = cache.filter((ponto) => ponto.id_temporario !== item.payload.id_temporario);
            await salvarPontosCache([created, ...semTemporario]);
            await removerPontoPendente(item.payload.id_temporario);

            // Limpar foto persistida localmente após upload bem-sucedido
            if (item.payload?.foto_uri) {
              try {
                const FileSystem = require('expo-file-system');
                const fs = FileSystem.default || FileSystem;
                if (fs?.documentDirectory && item.payload.foto_uri.startsWith(fs.documentDirectory)) {
                  await fs.deleteAsync(item.payload.foto_uri, { idempotent: true });
                }
              } catch (_cleanupErr) {
                // Limpeza não é crítica
              }
            }
          }
          sincronizadas += 1;
        } catch (error) {
          if (await this.lidarComNaoAutorizado(error)) {
            return { success: false, message: 'Sessão expirada. Faça login novamente.' };
          }
          const tentativas = (item.tentativas || 0) + 1;
          const retryable = error.status >= 500 || !error.status;
          if (retryable && tentativas < MAX_RETRY) {
            remaining.push({ ...item, tentativas });
          }
          await registrarSyncLog({
            nivel: retryable ? 'warn' : 'error',
            evento: 'sync_item_falhou',
            item: item.tipo,
            tentativas,
            erro: error.message,
          });
        }
      }

      await atualizarSyncQueue(remaining);
      await salvarUltimaSync(new Date().toISOString());

      try {
        await this.sincronizarDadosReferencia();
      } catch (error) {
        if (await this.lidarComNaoAutorizado(error)) {
          return { success: false, message: 'Sessão expirada. Faça login novamente.' };
        }
        await registrarSyncLog({ nivel: 'warn', evento: 'sync_referencia_falhou', erro: error.message });
        console.warn('[offlineService] Falha ao sincronizar dados de referência', error?.message || error);
      }

      return { success: true, sincronizadas, falhas: remaining.length };
    } catch (error) {
      if (await this.lidarComNaoAutorizado(error)) {
        return { success: false, message: 'Sessão expirada. Faça login novamente.' };
      }
      await registrarSyncLog({ nivel: 'error', evento: 'sync_geral_falhou', erro: error.message });
      console.error('[offlineService] Erro geral de sincronização', error);
      return { success: false, message: error.message || 'Erro ao sincronizar dados offline' };
    } finally {
      this.syncInProgress = false;
    }
  }

  async sincronizarDadosReferencia() {
    const since = await obterUltimaSync();
    const endpoint = since
      ? `${API_ENDPOINTS.offlineSync}?since=${encodeURIComponent(since)}`
      : API_ENDPOINTS.offlineSync;

    const data = await httpGet(endpoint);
    if (Array.isArray(data?.pontos)) {
      await salvarPontosCache(data.pontos);
    }
  }

  async obterStatusOffline() {
    const [online, pendentes, fila, ultimaSync, token] = await Promise.all([
      this.verificarConexao(),
      listarPontosPendentes(),
      listarSyncQueue(),
      obterUltimaSync(),
      getAuthToken(),
    ]);

    return {
      autenticado: !!token,
      online,
      pendentes: pendentes.length,
      fila: fila.length,
      ultimaSync,
    };
  }

  async limparPendenciasOffline() {
    await limparPontosPendentes();
    await registrarSyncLog({ nivel: 'info', evento: 'pendencias_offline_limpas' });
    return { success: true };
  }

  configurarSincronizacaoAutomatica(intervaloMinutos = 10) {
    this.pararSincronizacaoAutomatica();

    this.syncIntervalId = setInterval(() => this.sincronizar(), intervaloMinutos * 60 * 1000);
    this.netInfoUnsubscribe = NetInfo.addEventListener((state) => {
      if (state.isConnected && state.isInternetReachable !== false) {
        this.sincronizar();
      }
    });

    return () => this.pararSincronizacaoAutomatica();
  }

  pararSincronizacaoAutomatica() {
    if (this.syncIntervalId) {
      clearInterval(this.syncIntervalId);
      this.syncIntervalId = null;
    }
    if (this.netInfoUnsubscribe) {
      this.netInfoUnsubscribe();
      this.netInfoUnsubscribe = null;
    }
  }
}

export default new OfflineService();
