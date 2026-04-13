import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_ENDPOINTS } from '../config/api';
import { httpPost, setAuthToken } from './httpClient';

const normalizeAuthError = (error) => {
  if (error?.status === 401) return 'Credenciais inválidas.';
  if (error?.code === 'TIMEOUT') return 'Tempo de resposta excedido. Tente novamente.';
  if (error?.code === 'NETWORK') return 'Sem conexão com o servidor.';
  return error?.message || 'Falha na autenticação.';
};

class AuthService {
  async login({ username, password }) {
    try {
      const data = await httpPost(API_ENDPOINTS.login, { username, password });
      if (!data?.token) throw new Error('Token não retornado pelo servidor');
      await setAuthToken(data.token);
      if (data?.user_id) await AsyncStorage.setItem('userId', String(data.user_id));
      return { sucesso: true, data };
    } catch (error) {
      return { sucesso: false, erro: normalizeAuthError(error) };
    }
  }

  async register(payload) {
    try {
      const data = await httpPost(API_ENDPOINTS.register, payload);
      if (data?.token) await setAuthToken(data.token);
      if (data?.user_id) await AsyncStorage.setItem('userId', String(data.user_id));
      return { sucesso: true, data };
    } catch (error) {
      return { sucesso: false, erro: normalizeAuthError(error) };
    }
  }

  async logout() {
    // Tentar notificar o backend (não bloqueia se falhar)
    try {
      await httpPost(API_ENDPOINTS.logout, {});
    } catch (_) {
      // Logout local prossegue mesmo se backend estiver indisponível
    }
    await setAuthToken(null);
    await AsyncStorage.multiRemove(['userId']);
  }
}

export default new AuthService();
