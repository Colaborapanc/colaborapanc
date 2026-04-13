// mobile/src/services/mensagensService.js
// Serviço para gerenciar mensagens entre usuários

import api from './apiClient';

class MensagensService {
  /**
   * Busca todas as conversas do usuário
   */
  async buscarConversas() {
    try {
      const response = await api.get('/api/conversas/');
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar conversas:', error);
      throw error;
    }
  }

  /**
   * Cria nova conversa ou retorna existente
   */
  async criarConversa(outroUsuarioId) {
    try {
      const response = await api.post('/api/conversas/', {
        outro_usuario_id: outroUsuarioId,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao criar conversa:', error);
      throw error;
    }
  }

  /**
   * Busca mensagens de uma conversa
   */
  async buscarMensagens(conversaId) {
    try {
      const response = await api.get('/api/mensagens/', {
        params: { conversa_id: conversaId },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar mensagens:', error);
      throw error;
    }
  }

  /**
   * Envia nova mensagem
   */
  async enviarMensagem(conversaId, conteudo, imagem = null) {
    try {
      const formData = new FormData();
      formData.append('conversa_id', conversaId);
      formData.append('conteudo', conteudo);

      if (imagem) {
        formData.append('imagem', {
          uri: imagem.uri,
          type: 'image/jpeg',
          name: 'mensagem.jpg',
        });
      }

      const response = await api.post('/api/mensagens/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      throw error;
    }
  }

  /**
   * Marca mensagem como lida
   */
  async marcarComoLida(mensagemId) {
    try {
      await api.post(`/api/mensagens/${mensagemId}/marcar_lida/`);
    } catch (error) {
      console.error('Erro ao marcar como lida:', error);
      throw error;
    }
  }
}

export default new MensagensService();
