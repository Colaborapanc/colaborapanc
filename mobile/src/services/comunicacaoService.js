import { API_ENDPOINTS } from '../config/api';
import api from './apiClient';

export async function registrarPushToken({ token, plataforma, usuarioId }) {
  const response = await api.post(API_ENDPOINTS.pushToken, { token, plataforma, usuario_id: usuarioId });
  return response.data;
}

export async function listarNotificacoes(usuarioId) {
  const response = await api.get(API_ENDPOINTS.notificacoes, { params: usuarioId ? { usuario_id: usuarioId } : {} });
  return response.data;
}

export async function marcarNotificacaoLida(notificacaoId) {
  const response = await api.post(API_ENDPOINTS.notificacoes, { id: notificacaoId });
  return response.data;
}

export async function listarConversas(usuarioId) {
  const response = await api.get(API_ENDPOINTS.conversas, { params: usuarioId ? { usuario_id: usuarioId } : {} });
  return response.data;
}

export async function criarConversa(participantes) {
  const response = await api.post(API_ENDPOINTS.conversas, { participantes });
  return response.data;
}

export async function listarMensagens(conversaId) {
  const response = await api.get(API_ENDPOINTS.mensagens, { params: { conversa_id: conversaId } });
  return response.data;
}

export async function enviarMensagem({ conversaId, remetenteId, texto }) {
  const response = await api.post(API_ENDPOINTS.mensagens, { conversa_id: conversaId, remetente_id: remetenteId, texto });
  return response.data;
}

export async function registrarCompartilhamento({ pontoId, canal, url, usuarioId }) {
  const response = await api.post(API_ENDPOINTS.compartilhamentos, { ponto_id: pontoId, canal, url_compartilhada: url, usuario_id: usuarioId });
  return response.data;
}
