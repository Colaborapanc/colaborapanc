import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  PONTOS_CACHE: '@offline/pontos_cache',
  PONTOS_PENDING: '@offline/pontos_pending',
  SYNC_QUEUE: '@offline/sync_queue',
  SYNC_LOG: '@offline/sync_log',
  SPECIES_FOCUS: '@offline/species_focus',
  SPECIES_PACKAGES: '@offline/species_packages',
  IA_HISTORY: '@offline/ia_history',
  DRONE_MISSIONS: '@offline/drone_missions',
  DETECTION_HISTORY: '@offline/detection_history',
  SPECIES_BASE_META: '@offline/species_base_meta',
  LAST_SYNC: '@offline/last_sync',
};

const readJSON = async (key, fallback) => {
  const raw = await AsyncStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
};

const writeJSON = async (key, value) => AsyncStorage.setItem(key, JSON.stringify(value));

const normalizeCoordinates = (localizacao) => {
  if (!localizacao) return null;
  if (Array.isArray(localizacao) && localizacao.length === 2) {
    return { longitude: Number(localizacao[0]), latitude: Number(localizacao[1]) };
  }
  if (localizacao?.coordinates?.length === 2) {
    return { longitude: Number(localizacao.coordinates[0]), latitude: Number(localizacao.coordinates[1]) };
  }
  if (typeof localizacao.longitude === 'number' && typeof localizacao.latitude === 'number') {
    return { longitude: localizacao.longitude, latitude: localizacao.latitude };
  }
  return null;
};

const normalizePonto = (ponto) => {
  const coords = normalizeCoordinates(ponto.localizacao);
  const parte = Array.isArray(ponto.parte_comestivel_lista)
    ? ponto.parte_comestivel_lista
    : (ponto.parte_comestivel ? [ponto.parte_comestivel] : []);
  const frutificacao = Array.isArray(ponto.frutificacao_meses)
    ? ponto.frutificacao_meses
    : (ponto.epoca_frutificacao ? [ponto.epoca_frutificacao] : []);

  return {
    ...ponto,
    localizacao: coords ? [coords.longitude, coords.latitude] : null,
    comestibilidade_status: ponto.comestibilidade_status || 'nao_informado',
    parte_comestivel_lista: parte,
    frutificacao_meses: frutificacao,
    colheita_periodo: ponto.colheita_periodo || ponto.epoca_colheita || 'nao_informado',
    status_enriquecimento: ponto.status_enriquecimento || 'pendente',
    validacao_pendente_revisao_humana: Boolean(ponto.validacao_pendente_revisao_humana),
  };
};

export async function salvarPontosCache(pontos) {
  const normalized = (Array.isArray(pontos) ? pontos : []).map(normalizePonto);
  await writeJSON(KEYS.PONTOS_CACHE, {
    updatedAt: new Date().toISOString(),
    items: normalized,
  });
}

export async function carregarPontosCache() {
  const snapshot = await readJSON(KEYS.PONTOS_CACHE, { items: [] });
  return snapshot.items || [];
}

export async function carregarTimestampCache() {
  const snapshot = await readJSON(KEYS.PONTOS_CACHE, null);
  return snapshot?.updatedAt || null;
}

export async function salvarPontoPendente(ponto) {
  const pendentes = await readJSON(KEYS.PONTOS_PENDING, []);
  const idTemporario = ponto.id_temporario || `tmp_${Date.now()}`;
  const item = {
    ...normalizePonto(ponto),
    id_temporario: idTemporario,
    status_sync: 'pendente',
    criado_em_local: new Date().toISOString(),
  };
  pendentes.push(item);
  await writeJSON(KEYS.PONTOS_PENDING, pendentes);
  return item;
}

export async function listarPontosPendentes() {
  return readJSON(KEYS.PONTOS_PENDING, []);
}

export async function removerPontoPendente(idTemporario) {
  const pendentes = await readJSON(KEYS.PONTOS_PENDING, []);
  await writeJSON(KEYS.PONTOS_PENDING, pendentes.filter((item) => item.id_temporario !== idTemporario));
}

export async function limparPontosPendentes() {
  await writeJSON(KEYS.PONTOS_PENDING, []);
  await writeJSON(KEYS.SYNC_QUEUE, []);
}

export async function adicionarSyncQueue(item) {
  const queue = await readJSON(KEYS.SYNC_QUEUE, []);
  const dedupeKey = `${item.tipo}:${item.idempotencyKey || ''}`;
  const filtered = queue.filter((q) => `${q.tipo}:${q.idempotencyKey || ''}` !== dedupeKey);
  filtered.push({ ...item, enfileirado_em: new Date().toISOString(), tentativas: item.tentativas || 0 });
  await writeJSON(KEYS.SYNC_QUEUE, filtered);
  return filtered.length;
}

export async function listarSyncQueue() {
  return readJSON(KEYS.SYNC_QUEUE, []);
}

export async function atualizarSyncQueue(items) {
  await writeJSON(KEYS.SYNC_QUEUE, items);
}

export async function registrarSyncLog(evento) {
  const logs = await readJSON(KEYS.SYNC_LOG, []);
  logs.unshift({ ...evento, timestamp: new Date().toISOString() });
  await writeJSON(KEYS.SYNC_LOG, logs.slice(0, 200));
}

export async function listarSyncLogs() {
  return readJSON(KEYS.SYNC_LOG, []);
}

export async function salvarUltimaSync(isoDate) {
  await AsyncStorage.setItem(KEYS.LAST_SYNC, isoDate);
}

export async function obterUltimaSync() {
  return AsyncStorage.getItem(KEYS.LAST_SYNC);
}

export async function upsertCollection(key, items, idField = 'id') {
  const current = await readJSON(key, []);
  const map = new Map(current.map((item) => [String(item[idField]), item]));
  for (const item of items) map.set(String(item[idField]), item);
  const merged = Array.from(map.values());
  await writeJSON(key, merged);
  return merged;
}

export const OFFLINE_KEYS = KEYS;

export async function salvarSpeciesBaseMeta(meta) {
  await writeJSON(KEYS.SPECIES_BASE_META, meta);
}

export async function obterSpeciesBaseMeta() {
  return readJSON(KEYS.SPECIES_BASE_META, null);
}

export async function salvarHistoricoDeteccao(item) {
  const history = await readJSON(KEYS.DETECTION_HISTORY, []);
  history.unshift(item);
  await writeJSON(KEYS.DETECTION_HISTORY, history.slice(0, 500));
}

export async function listarHistoricoDeteccao() {
  return readJSON(KEYS.DETECTION_HISTORY, []);
}

export async function adicionarPontoDetectadoCache(ponto) {
  const snapshot = await readJSON(KEYS.PONTOS_CACHE, { items: [], updatedAt: null });
  const item = normalizePonto(ponto);
  snapshot.items = [item, ...(snapshot.items || [])];
  snapshot.updatedAt = new Date().toISOString();
  await writeJSON(KEYS.PONTOS_CACHE, snapshot);
  return item;
}
