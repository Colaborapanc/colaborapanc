import { LogBox } from 'react-native';
LogBox.ignoreLogs(['Invalid prop `style` supplied to `React.Fragment`']);

import React, { useEffect, useState } from 'react';
import { Alert, StyleSheet, Text, View, Image, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import offlineService from '../services/offlineService';

const QuickAction = ({ icon, label, color, onPress, badge }) => (
  <TouchableOpacity style={styles.actionCard} onPress={onPress} activeOpacity={0.7}>
    <View style={[styles.actionIconContainer, { backgroundColor: color + '15' }]}>
      <Ionicons name={icon} size={26} color={color} />
      {badge > 0 && (
        <View style={styles.actionBadge}>
          <Text style={styles.actionBadgeText}>{badge}</Text>
        </View>
      )}
    </View>
    <Text style={styles.actionLabel}>{label}</Text>
  </TouchableOpacity>
);

export default function HomeScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [status, setStatus] = useState({ online: true, pendentes: 0, fila: 0, autenticado: true });
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const load = async () => setStatus(await offlineService.obterStatusOffline());
    load();
    const i = setInterval(load, 8000);
    return () => clearInterval(i);
  }, []);

  const navegarComAuth = (rota) => {
    if (!status.autenticado) {
      Alert.alert('Login necessário', 'Faça login para usar funcionalidades online e sincronização.');
      return;
    }
    navigation.navigate(rota);
  };

  const sincronizarAgora = async () => {
    setSyncing(true);
    try {
      const resultado = await offlineService.sincronizar();
      Alert.alert(resultado.success ? 'Sincronização concluída' : 'Sincronização', resultado.message || `Sincronizadas: ${resultado.sincronizadas || 0} | Falhas: ${resultado.falhas || 0}`);
      setStatus(await offlineService.obterStatusOffline());
    } finally {
      setSyncing(false);
    }
  };

  const confirmarLimparPendencias = () => {
    Alert.alert(
      'Excluir pendências offline?',
      'Essa ação remove os cadastros pendentes que ainda não foram sincronizados.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Excluir',
          style: 'destructive',
          onPress: async () => {
            await offlineService.limparPendenciasOffline();
            setStatus(await offlineService.obterStatusOffline());
          },
        },
      ]
    );
  };

  const hasPending = status.pendentes > 0 || status.fila > 0;

  return (
    <ScrollView
      style={styles.scrollView}
      contentContainerStyle={[styles.container, { paddingTop: Math.max(16, insets.top), paddingBottom: Math.max(24, insets.bottom + 16) }]}
    >
      {/* Header / Branding */}
      <View style={styles.headerSection}>
        <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
        <View>
          <Text style={styles.title}>ColaboraPANC</Text>
          <Text style={styles.subtitle}>Mapeamento colaborativo de PANCs</Text>
        </View>
      </View>

      {/* Status */}
      <View style={[styles.statusCard, status.online ? styles.statusOnline : styles.statusOffline]}>
        <View style={styles.statusHeader}>
          <View style={styles.statusDot}>
            <View style={[styles.dot, { backgroundColor: status.online ? '#16A34A' : '#D97706' }]} />
          </View>
          <Text style={styles.statusTitle}>{status.online ? 'Conectado' : 'Modo Offline'}</Text>
        </View>

        {hasPending && (
          <View style={styles.statusCounters}>
            <View style={styles.counterItem}>
              <Ionicons name="time-outline" size={16} color="#64748B" />
              <Text style={styles.counterText}>{status.pendentes} pendentes</Text>
            </View>
            <View style={styles.counterItem}>
              <Ionicons name="sync-outline" size={16} color="#64748B" />
              <Text style={styles.counterText}>{status.fila} na fila</Text>
            </View>
          </View>
        )}

        {hasPending && (
          <View style={styles.syncRow}>
            <TouchableOpacity
              style={[styles.syncButton, syncing && { opacity: 0.6 }]}
              onPress={sincronizarAgora}
              disabled={syncing}
            >
              <Ionicons name="sync" size={16} color="#fff" />
              <Text style={styles.syncButtonText}>{syncing ? 'Sincronizando...' : 'Sincronizar'}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.clearButton} onPress={confirmarLimparPendencias}>
              <Ionicons name="trash-outline" size={16} color="#DC2626" />
              <Text style={styles.clearButtonText}>Limpar</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {!status.autenticado && (
        <View style={styles.authWarning}>
          <Ionicons name="warning-outline" size={20} color="#DC2626" />
          <Text style={styles.authWarningText}>Sessão expirada. Faça login para sincronizar dados.</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Login')}>
            <Text style={styles.authWarningLink}>Entrar</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Quick Actions - Grid */}
      <Text style={styles.sectionTitle}>Ações Rápidas</Text>
      <View style={styles.actionsGrid}>
        <QuickAction icon="map" label="Mapa" color="#0EA5E9" onPress={() => navegarComAuth('Mapa')} />
        <QuickAction icon="add-circle" label="Cadastrar" color="#1B9E5A" onPress={() => navegarComAuth('CadastroPonto')} />
        <QuickAction icon="camera" label="Identificar" color="#8B5CF6" onPress={() => navigation.navigate('IdentificarPlanta')} />
        <QuickAction icon="shield-checkmark" label="Revisão" color="#D97706" onPress={() => navegarComAuth('Revisor')} />
        <QuickAction icon="cloud-download" label="Base Offline" color="#0EA5E9" onPress={() => navigation.navigate('PlantasOffline')} />
        <QuickAction icon="notifications" label="Alertas" color="#EA580C" onPress={() => navegarComAuth('Notificacoes')} badge={0} />
        <QuickAction icon="person" label="Perfil" color="#64748B" onPress={() => navegarComAuth('Perfil')} />
      </View>

      {/* Info */}
      <View style={styles.infoCard}>
        <Ionicons name="information-circle-outline" size={20} color="#0EA5E9" />
        <Text style={styles.infoText}>
          Use a câmera IA para identificar plantas e contribua cadastrando novos pontos de PANCs no mapa.
        </Text>
      </View>

      <Text style={styles.credits}>ColaboraPANC 2026</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: { flex: 1, backgroundColor: '#F8FAFC' },
  container: { padding: 20 },

  headerSection: { flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 20 },
  logo: { width: 64, height: 64, borderRadius: 16, borderWidth: 1, borderColor: '#E2E8F0', backgroundColor: '#fff' },
  title: { fontSize: 28, fontWeight: '800', color: '#0F172A', letterSpacing: 0.5 },
  subtitle: { fontSize: 14, color: '#64748B', fontWeight: '500', marginTop: 2 },

  statusCard: { borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 1 },
  statusOnline: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' },
  statusOffline: { backgroundColor: '#FFFBEB', borderColor: '#FDE68A' },
  statusHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  statusDot: { width: 24, height: 24, borderRadius: 12, backgroundColor: 'rgba(0,0,0,0.05)', justifyContent: 'center', alignItems: 'center' },
  dot: { width: 10, height: 10, borderRadius: 5 },
  statusTitle: { fontWeight: '700', fontSize: 15, color: '#0F172A' },
  statusCounters: { flexDirection: 'row', gap: 16, marginTop: 10 },
  counterItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  counterText: { color: '#64748B', fontSize: 13 },
  syncRow: { flexDirection: 'row', gap: 10, marginTop: 12 },
  syncButton: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#1B9E5A', paddingVertical: 8, paddingHorizontal: 14, borderRadius: 10 },
  syncButtonText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  clearButton: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#FEE2E2', paddingVertical: 8, paddingHorizontal: 14, borderRadius: 10 },
  clearButtonText: { color: '#DC2626', fontWeight: '700', fontSize: 13 },

  authWarning: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#FEF2F2', borderRadius: 12, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: '#FECACA' },
  authWarningText: { color: '#991B1B', fontSize: 13, flex: 1 },
  authWarningLink: { color: '#1B9E5A', fontWeight: '700', fontSize: 14 },

  sectionTitle: { fontSize: 17, fontWeight: '700', color: '#0F172A', marginBottom: 12, marginTop: 8 },

  actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 20 },
  actionCard: {
    width: '30%',
    flexGrow: 1,
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#F1F5F9',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  actionIconContainer: { width: 52, height: 52, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginBottom: 8, position: 'relative' },
  actionBadge: { position: 'absolute', top: -4, right: -4, backgroundColor: '#DC2626', width: 18, height: 18, borderRadius: 9, justifyContent: 'center', alignItems: 'center' },
  actionBadgeText: { color: '#fff', fontSize: 10, fontWeight: '800' },
  actionLabel: { color: '#475569', fontWeight: '600', fontSize: 13, textAlign: 'center' },

  infoCard: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, backgroundColor: '#EFF6FF', borderRadius: 14, padding: 14, marginBottom: 20, borderWidth: 1, borderColor: '#BFDBFE' },
  infoText: { color: '#1E40AF', fontSize: 13, lineHeight: 19, flex: 1 },

  credits: { fontSize: 12, color: '#CBD5E1', textAlign: 'center', marginTop: 8 },
});
