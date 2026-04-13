// mobile/src/screens/NotificacoesScreen.js
// Tela de notificações

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
} from 'react-native';
import notificacoesService from '../services/notificacoesService';
import i18n from '../services/i18nService';

export default function NotificacoesScreen({ navigation }) {
  const [notificacoes, setNotificacoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    carregarNotificacoes();
  }, []);

  const carregarNotificacoes = async () => {
    try {
      setLoading(true);
      const dados = await notificacoesService.buscarNotificacoes();
      setNotificacoes(dados);
    } catch (error) {
      Alert.alert(i18n.t('app.error'), 'Erro ao carregar notificações');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await carregarNotificacoes();
    setRefreshing(false);
  };

  const marcarTodasLidas = async () => {
    try {
      await notificacoesService.marcarTodasComoLidas();
      await carregarNotificacoes();
      Alert.alert(i18n.t('app.success'), 'Todas marcadas como lidas');
    } catch (error) {
      Alert.alert(i18n.t('app.error'), 'Erro ao marcar como lidas');
    }
  };

  const abrirNotificacao = async (notificacao) => {
    if (!notificacao.lida) {
      await notificacoesService.marcarComoLida(notificacao.id);
    }

    // Navega para o link (se houver)
    if (notificacao.link) {
      // Implementar navegação baseada no link
      console.log('Navegar para:', notificacao.link);
    }
  };

  const renderNotificacao = ({ item }) => (
    <TouchableOpacity
      style={[
        styles.notificacaoItem,
        !item.lida && styles.notificacaoNaoLida,
      ]}
      onPress={() => abrirNotificacao(item)}
    >
      <View style={styles.notificacaoIcon}>
        <Text style={styles.notificacaoIconTexto}>
          {getTipoIcon(item.tipo)}
        </Text>
      </View>
      <View style={styles.notificacaoConteudo}>
        <Text style={styles.notificacaoTitulo}>{item.titulo}</Text>
        <Text style={styles.notificacaoMensagem} numberOfLines={2}>
          {item.mensagem}
        </Text>
        <Text style={styles.notificacaoData}>
          {formatarData(item.criada_em)}
        </Text>
      </View>
      {!item.lida && <View style={styles.indicadorNaoLida} />}
    </TouchableOpacity>
  );

  const getTipoIcon = (tipo) => {
    const icons = {
      novo_ponto: '📍',
      validacao: '✅',
      badge: '🏆',
      missao: '🎯',
      nivel: '⭐',
      mensagem: '💬',
      alerta: '⚠️',
      evento: '📅',
      sistema: 'ℹ️',
    };
    return icons[tipo] || 'ℹ️';
  };

  const formatarData = (dataISO) => {
    const data = new Date(dataISO);
    const agora = new Date();
    const diff = Math.floor((agora - data) / 1000); // diferença em segundos

    if (diff < 60) return 'Agora';
    if (diff < 3600) return `${Math.floor(diff / 60)}m atrás`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d atrás`;

    return data.toLocaleDateString('pt-BR');
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>{i18n.t('app.loading')}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.titulo}>{i18n.t('notifications.title')}</Text>
        {notificacoes.some((n) => !n.lida) && (
          <TouchableOpacity onPress={marcarTodasLidas}>
            <Text style={styles.marcarTodasBtn}>
              {i18n.t('notifications.markAllRead')}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {notificacoes.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>
            {i18n.t('notifications.empty')}
          </Text>
        </View>
      ) : (
        <FlatList
          data={notificacoes}
          renderItem={renderNotificacao}
          keyExtractor={(item) => item.id.toString()}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  titulo: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  marcarTodasBtn: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: '600',
  },
  notificacaoItem: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 16,
    marginVertical: 4,
    marginHorizontal: 8,
    borderRadius: 8,
    elevation: 1,
  },
  notificacaoNaoLida: {
    backgroundColor: '#E8F5E9',
  },
  notificacaoIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#f0f0f0',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  notificacaoIconTexto: {
    fontSize: 24,
  },
  notificacaoConteudo: {
    flex: 1,
  },
  notificacaoTitulo: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  notificacaoMensagem: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  notificacaoData: {
    fontSize: 12,
    color: '#999',
  },
  indicadorNaoLida: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#4CAF50',
    marginLeft: 8,
    alignSelf: 'center',
  },
  loadingText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    textAlign: 'center',
  },
});
