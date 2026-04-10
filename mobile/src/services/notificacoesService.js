// Serviço para gerenciar notificações (compatível com Expo Go + dev build)

import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import api from './apiClient';
import { API_ENDPOINTS } from '../config/api';

const isExpoGo = Constants.appOwnership === 'expo';

let notificationsModule = null;
let deviceModule = null;
let handlerConfigured = false;

const ensureNotificationsReady = async () => {
  if (!notificationsModule) {
    notificationsModule = await import('expo-notifications');
  }
  if (!deviceModule) {
    deviceModule = await import('expo-device');
  }

  if (!handlerConfigured && typeof notificationsModule?.setNotificationHandler === 'function') {
    notificationsModule.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
    handlerConfigured = true;
  }

  return { Notifications: notificationsModule, Device: deviceModule };
};

class NotificacoesService {
  constructor() {
    this.notificationListener = null;
    this.responseListener = null;
  }

  async registrarDispositivo() {
    try {
      // Push remoto em Android não funciona no Expo Go (SDK 53+)
      if (isExpoGo && Platform.OS === 'android') {
        console.log('Push remoto desativado no Expo Go (Android).');
        return null;
      }

      const { Notifications, Device } = await ensureNotificationsReady();

      if (!Device.isDevice) return null;

      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      if (finalStatus !== 'granted') return null;

      const projectId = Constants?.expoConfig?.extra?.eas?.projectId || Constants?.easConfig?.projectId || process.env.EXPO_PUBLIC_EAS_PROJECT_ID;
      const tokenResp = await Notifications.getExpoPushTokenAsync(projectId ? { projectId } : undefined);
      const token = tokenResp?.data;
      if (!token) return null;

      const plataforma = Platform.OS === 'ios' ? 'ios' : 'android';
      await api.post(API_ENDPOINTS.pushToken, { token, plataforma });
      return token;
    } catch (error) {
      console.error('Erro ao registrar dispositivo:', error);
      return null;
    }
  }

  async configurarListeners(onNotificationReceived, onNotificationTapped) {
    const { Notifications } = await ensureNotificationsReady();

    this.notificationListener = Notifications.addNotificationReceivedListener((notification) => {
      if (onNotificationReceived) onNotificationReceived(notification);
    });

    this.responseListener = Notifications.addNotificationResponseReceivedListener((response) => {
      if (onNotificationTapped) onNotificationTapped(response);
    });
  }

  async removerListeners() {
    const { Notifications } = await ensureNotificationsReady();
    if (this.notificationListener) Notifications.removeNotificationSubscription(this.notificationListener);
    if (this.responseListener) Notifications.removeNotificationSubscription(this.responseListener);
  }

  async buscarNotificacoes() {
    const usuarioId = await AsyncStorage.getItem('userId');
    const response = await api.get(API_ENDPOINTS.notificacoes, { params: usuarioId ? { usuario_id: usuarioId } : {} });
    return Array.isArray(response.data) ? response.data : [];
  }

  async buscarNaoLidas() {
    const notificacoes = await this.buscarNotificacoes();
    return notificacoes.filter((item) => !item.lida && !item.lida_em);
  }

  async marcarComoLida(notificacaoId) {
    return api.patch(`${API_ENDPOINTS.notificacoes}${notificacaoId}/`, { lida: true });
  }

  async marcarTodasComoLidas() {
    const notificacoes = await this.buscarNaoLidas();
    await Promise.all(notificacoes.map((item) => this.marcarComoLida(item.id)));
  }

  async obterContador() {
    const naoLidas = await this.buscarNaoLidas();
    return naoLidas.length;
  }

  async agendarNotificacaoLocal(titulo, corpo, segundos = 5) {
    try {
      const { Notifications } = await ensureNotificationsReady();
      await Notifications.scheduleNotificationAsync({
        content: { title: titulo, body: corpo, sound: true },
        trigger: { type: 'timeInterval', seconds: Math.max(1, segundos), repeats: false },
      });
    } catch (error) {
      console.error('Erro ao agendar notificação local:', error);
    }
  }
}

export default new NotificacoesService();
