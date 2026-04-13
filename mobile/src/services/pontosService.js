import { API_ENDPOINTS } from '../config/api';
import api from './apiClient';

export async function buscarPontosComFiltros(filtros = {}) {
  const params = new URLSearchParams();
  Object.entries(filtros).forEach(([chave, valor]) => {
    if (valor !== undefined && valor !== null && valor !== '') {
      params.append(chave, valor);
    }
  });
  const response = await api.get(API_ENDPOINTS.pontos, { params: Object.fromEntries(params.entries()) });
  return response.data;
}

export async function sincronizarOffline(desde) {
  const response = await api.get(API_ENDPOINTS.offlineSync, { params: desde ? { since: desde } : {} });
  return response.data;
}
