// mobile/src/services/i18nService.js
// Serviço de internacionalização (i18n)

import AsyncStorage from '@react-native-async-storage/async-storage';
import { I18n } from 'i18n-js';
import * as Localization from 'expo-localization';

// Traduções
const translations = {
  'pt-BR': {
    app: {
      name: 'ColaboraPANC',
      loading: 'Carregando...',
      error: 'Erro',
      success: 'Sucesso',
      cancel: 'Cancelar',
      confirm: 'Confirmar',
      save: 'Salvar',
      delete: 'Excluir',
      edit: 'Editar',
      back: 'Voltar',
      next: 'Próximo',
      finish: 'Finalizar',
      search: 'Buscar',
      filter: 'Filtrar',
    },
    auth: {
      login: 'Entrar',
      logout: 'Sair',
      register: 'Cadastrar',
      username: 'Usuário',
      email: 'E-mail',
      password: 'Senha',
      forgotPassword: 'Esqueci minha senha',
      loginSuccess: 'Login realizado com sucesso!',
      loginError: 'Erro ao fazer login',
    },
    map: {
      title: 'Mapa de PANCs',
      searchLocation: 'Buscar localização',
      myLocation: 'Minha localização',
      filters: 'Filtros',
      nearbyPoints: 'Pontos próximos',
    },
    points: {
      title: 'Pontos',
      new: 'Novo Ponto',
      details: 'Detalhes do Ponto',
      name: 'Nome',
      location: 'Localização',
      description: 'Descrição',
      photo: 'Foto',
      contributor: 'Colaborador',
      city: 'Cidade',
      state: 'Estado',
      createSuccess: 'Ponto criado com sucesso!',
      createError: 'Erro ao criar ponto',
    },
    notifications: {
      title: 'Notificações',
      empty: 'Nenhuma notificação',
      markAllRead: 'Marcar todas como lidas',
      newPoint: 'Novo ponto cadastrado',
      validation: 'Seu ponto foi validado',
      newBadge: 'Nova conquista desbloqueada!',
      newMessage: 'Nova mensagem recebida',
    },
    messages: {
      title: 'Mensagens',
      conversations: 'Conversas',
      empty: 'Nenhuma conversa',
      newConversation: 'Nova conversa',
      typeMessage: 'Digite uma mensagem...',
      send: 'Enviar',
    },
    routes: {
      title: 'Rotas',
      myRoutes: 'Minhas Rotas',
      new: 'Nova Rota',
      name: 'Nome da Rota',
      description: 'Descrição',
      points: 'Pontos',
      addPoint: 'Adicionar Ponto',
      optimize: 'Otimizar Rota',
      distance: 'Distância',
      estimatedTime: 'Tempo Estimado',
      visited: 'Visitado',
      markVisited: 'Marcar como visitado',
    },
    recommendations: {
      title: 'Recomendações',
      forYou: 'Recomendadas para você',
      empty: 'Nenhuma recomendação disponível',
      reason: 'Por que recomendamos',
      viewDetails: 'Ver detalhes',
    },
    settings: {
      title: 'Configurações',
      language: 'Idioma',
      notifications: 'Notificações',
      enablePush: 'Ativar notificações push',
      enableMessages: 'Notificar mensagens',
      enableAlerts: 'Notificar alertas climáticos',
      privacy: 'Privacidade',
      publicProfile: 'Perfil público',
      showLocation: 'Mostrar localização exata',
      allowMessages: 'Permitir mensagens de outros usuários',
    },
    offline: {
      mode: 'Modo Offline',
      noConnection: 'Sem conexão com a internet',
      usingCache: 'Usando dados em cache',
      syncPending: 'Sincronização pendente',
      syncNow: 'Sincronizar agora',
      lastSync: 'Última sincronização',
    },
    share: {
      title: 'Compartilhar',
      sharePoint: 'Compartilhar ponto',
      shareRoute: 'Compartilhar rota',
      shareAchievement: 'Compartilhar conquista',
      inviteFriends: 'Convidar amigos',
    },
  },
  en: {
    app: {
      name: 'ColaboraPANC',
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      cancel: 'Cancel',
      confirm: 'Confirm',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      back: 'Back',
      next: 'Next',
      finish: 'Finish',
      search: 'Search',
      filter: 'Filter',
    },
    auth: {
      login: 'Login',
      logout: 'Logout',
      register: 'Register',
      username: 'Username',
      email: 'Email',
      password: 'Password',
      forgotPassword: 'Forgot password',
      loginSuccess: 'Login successful!',
      loginError: 'Login error',
    },
    map: {
      title: 'PANC Map',
      searchLocation: 'Search location',
      myLocation: 'My location',
      filters: 'Filters',
      nearbyPoints: 'Nearby points',
    },
    points: {
      title: 'Points',
      new: 'New Point',
      details: 'Point Details',
      name: 'Name',
      location: 'Location',
      description: 'Description',
      photo: 'Photo',
      contributor: 'Contributor',
      city: 'City',
      state: 'State',
      createSuccess: 'Point created successfully!',
      createError: 'Error creating point',
    },
    notifications: {
      title: 'Notifications',
      empty: 'No notifications',
      markAllRead: 'Mark all as read',
      newPoint: 'New point registered',
      validation: 'Your point has been validated',
      newBadge: 'New achievement unlocked!',
      newMessage: 'New message received',
    },
    messages: {
      title: 'Messages',
      conversations: 'Conversations',
      empty: 'No conversations',
      newConversation: 'New conversation',
      typeMessage: 'Type a message...',
      send: 'Send',
    },
    routes: {
      title: 'Routes',
      myRoutes: 'My Routes',
      new: 'New Route',
      name: 'Route Name',
      description: 'Description',
      points: 'Points',
      addPoint: 'Add Point',
      optimize: 'Optimize Route',
      distance: 'Distance',
      estimatedTime: 'Estimated Time',
      visited: 'Visited',
      markVisited: 'Mark as visited',
    },
    recommendations: {
      title: 'Recommendations',
      forYou: 'Recommended for you',
      empty: 'No recommendations available',
      reason: 'Why we recommend',
      viewDetails: 'View details',
    },
    settings: {
      title: 'Settings',
      language: 'Language',
      notifications: 'Notifications',
      enablePush: 'Enable push notifications',
      enableMessages: 'Notify messages',
      enableAlerts: 'Notify weather alerts',
      privacy: 'Privacy',
      publicProfile: 'Public profile',
      showLocation: 'Show exact location',
      allowMessages: 'Allow messages from other users',
    },
    offline: {
      mode: 'Offline Mode',
      noConnection: 'No internet connection',
      usingCache: 'Using cached data',
      syncPending: 'Sync pending',
      syncNow: 'Sync now',
      lastSync: 'Last sync',
    },
    share: {
      title: 'Share',
      sharePoint: 'Share point',
      shareRoute: 'Share route',
      shareAchievement: 'Share achievement',
      inviteFriends: 'Invite friends',
    },
  },
  es: {
    app: {
      name: 'ColaboraPANC',
      loading: 'Cargando...',
      error: 'Error',
      success: 'Éxito',
      cancel: 'Cancelar',
      confirm: 'Confirmar',
      save: 'Guardar',
      delete: 'Eliminar',
      edit: 'Editar',
      back: 'Volver',
      next: 'Siguiente',
      finish: 'Finalizar',
      search: 'Buscar',
      filter: 'Filtrar',
    },
    auth: {
      login: 'Iniciar sesión',
      logout: 'Cerrar sesión',
      register: 'Registrarse',
      username: 'Usuario',
      email: 'Correo electrónico',
      password: 'Contraseña',
      forgotPassword: 'Olvidé mi contraseña',
      loginSuccess: '¡Inicio de sesión exitoso!',
      loginError: 'Error al iniciar sesión',
    },
    map: {
      title: 'Mapa de PANCs',
      searchLocation: 'Buscar ubicación',
      myLocation: 'Mi ubicación',
      filters: 'Filtros',
      nearbyPoints: 'Puntos cercanos',
    },
    // ... (adicionar mais traduções conforme necessário)
  },
};

class I18nService {
  constructor() {
    const safeTranslations = translations && typeof translations === 'object' ? translations : { 'pt-BR': {} };
    this.i18n = new I18n(safeTranslations);
    this.STORAGE_KEY = '@language_preference';

    // Configurações padrão
    this.i18n.enableFallback = true;
    this.i18n.defaultLocale = 'pt-BR';

    this.inicializar();
  }

  /**
   * Inicializa o serviço de i18n
   */
  async inicializar() {
    try {
      // Tenta carregar idioma salvo
      const idiomasSalvo = await AsyncStorage.getItem(this.STORAGE_KEY);

      if (idiomasSalvo) {
        this.i18n.locale = idiomasSalvo;
      } else {
        // Usa idioma do dispositivo
        const locales = typeof Localization.getLocales === 'function' ? Localization.getLocales() : (Localization.locales || []);
        const idioma = locales?.[0]?.languageTag || locales?.[0]?.languageCode || 'pt-BR';
        this.i18n.locale = this.mapearIdioma(idioma);
      }
    } catch (error) {
      console.error('Erro ao inicializar i18n:', error);
      this.i18n.locale = 'pt-BR';
    }
  }

  /**
   * Mapeia tag de idioma para código suportado
   */
  mapearIdioma(idioma) {
    if (!idioma || typeof idioma !== 'string') return 'pt-BR';
    if (idioma.startsWith('pt')) return 'pt-BR';
    if (idioma.startsWith('en')) return 'en';
    if (idioma.startsWith('es')) return 'es';
    return 'pt-BR';
  }

  /**
   * Obtém tradução
   */
  t(chave, opcoes = {}) {
    try {
      return this.i18n.t(chave, opcoes);
    } catch (error) {
      console.error('Erro ao traduzir chave:', chave, error);
      return chave;
    }
  }

  /**
   * Altera idioma
   */
  async alterarIdioma(idioma) {
    try {
      this.i18n.locale = idioma;
      await AsyncStorage.setItem(this.STORAGE_KEY, idioma);
    } catch (error) {
      console.error('Erro ao alterar idioma:', error);
    }
  }

  /**
   * Obtém idioma atual
   */
  obterIdiomaAtual() {
    return this.i18n.locale;
  }

  /**
   * Obtém idiomas disponíveis
   */
  obterIdiomasDisponiveis() {
    return [
      { codigo: 'pt-BR', nome: 'Português (Brasil)', nativo: 'Português' },
      { codigo: 'en', nome: 'English', nativo: 'English' },
      { codigo: 'es', nome: 'Español', nativo: 'Español' },
    ];
  }
}

export default new I18nService();
