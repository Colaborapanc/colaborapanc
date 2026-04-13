import { API_ENDPOINTS } from '../config/api';
import { httpGet, httpPost } from './httpClient';

class EnrichmentService {
  async carregarPonto(id) {
    return httpGet(API_ENDPOINTS.pontoDetalhe(id));
  }

  async revalidarPonto(id) {
    return httpPost(API_ENDPOINTS.pontoRevalidar(id), {});
  }
}

export default new EnrichmentService();
