// mobile/src/services/rotasService.js
// Serviço para gerenciar rotas de PANCs

import api from './apiClient';

class RotasService {
  /**
   * Busca todas as rotas do usuário
   */
  async buscarRotas() {
    try {
      const response = await api.get('/api/rotas/');
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar rotas:', error);
      throw error;
    }
  }

  /**
   * Cria nova rota
   */
  async criarRota(nome, descricao, publica = false) {
    try {
      const response = await api.post('/api/rotas/', {
        nome,
        descricao,
        publica,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao criar rota:', error);
      throw error;
    }
  }

  /**
   * Atualiza rota existente
   */
  async atualizarRota(rotaId, dados) {
    try {
      const response = await api.patch(`/api/rotas/${rotaId}/`, dados);
      return response.data;
    } catch (error) {
      console.error('Erro ao atualizar rota:', error);
      throw error;
    }
  }

  /**
   * Deleta uma rota
   */
  async deletarRota(rotaId) {
    try {
      await api.delete(`/api/rotas/${rotaId}/`);
    } catch (error) {
      console.error('Erro ao deletar rota:', error);
      throw error;
    }
  }

  /**
   * Adiciona ponto à rota
   */
  async adicionarPonto(rotaId, pontoId) {
    try {
      const response = await api.post(`/api/rotas/${rotaId}/adicionar_ponto/`, {
        ponto_id: pontoId,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao adicionar ponto:', error);
      throw error;
    }
  }

  /**
   * Marca ponto como visitado
   */
  async marcarVisitado(rotaId, pontoRotaId) {
    try {
      const response = await api.post(`/api/rotas/${rotaId}/marcar_visitado/`, {
        ponto_rota_id: pontoRotaId,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao marcar visitado:', error);
      throw error;
    }
  }

  /**
   * Busca pontos próximos
   */
  async buscarPontosProximos(latitude, longitude, raio = 10) {
    try {
      const response = await api.get('/api/rotas/pontos-proximos/', {
        params: {
          latitude,
          longitude,
          raio,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar pontos próximos:', error);
      throw error;
    }
  }

  /**
   * Calcula rota otimizada entre pontos
   */
  async calcularRota(pontos) {
    try {
      const response = await api.post('/api/rotas/calcular/', {
        pontos,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao calcular rota:', error);
      throw error;
    }
  }

  /**
   * Sugere rota automática baseada na localização
   */
  async sugerirRota(latitude, longitude, numPontos = 5, raio = 20) {
    try {
      const response = await api.post('/api/rotas/sugerir/', {
        latitude,
        longitude,
        num_pontos: numPontos,
        raio,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao sugerir rota:', error);
      throw error;
    }
  }
}

export default new RotasService();
