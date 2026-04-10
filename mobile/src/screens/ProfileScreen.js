import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, TextInput, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { API_ENDPOINTS } from '../config/api';
import { setAuthToken } from '../services/httpClient';
import api from '../services/apiClient';
import authService from '../services/authService';

const StatCard = ({ icon, color, value, label }) => (
  <View style={styles.statCard}>
    <View style={[styles.statIconBg, { backgroundColor: color + '15' }]}>
      <Ionicons name={icon} size={24} color={color} />
    </View>
    <Text style={styles.statValue}>{value}</Text>
    <Text style={styles.statLabel}>{label}</Text>
  </View>
);

const InfoRow = ({ icon, label, value }) => (
  <View style={styles.infoRow}>
    <View style={styles.infoIconBg}>
      <Ionicons name={icon} size={18} color="#64748B" />
    </View>
    <View style={styles.infoContent}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value || 'Não informado'}</Text>
    </View>
  </View>
);

export default function ProfileScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [senhaAtual, setSenhaAtual] = useState('');
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmaSenha, setConfirmaSenha] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await api.get(API_ENDPOINTS.userProfile);
      setProfile(response.data || {});
    } catch (error) {
      try {
        const fallback = await api.get(API_ENDPOINTS.perfil);
        const data = fallback.data;
        const parsed = Array.isArray(data) ? data[0] : data?.results?.[0] || data;
        setProfile(parsed || {});
      } catch (fallbackError) {
        setErrorMessage(fallbackError?.status === 401 ? 'Sessão expirada. Faça login novamente.' : 'Falha ao carregar perfil.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!senhaAtual || !novaSenha) {
      Alert.alert('Erro', 'Preencha todos os campos.');
      return;
    }
    if (novaSenha !== confirmaSenha) {
      Alert.alert('Erro', 'Nova senha e confirmação não conferem.');
      return;
    }
    if (novaSenha.length < 6) {
      Alert.alert('Erro', 'Nova senha deve ter pelo menos 6 caracteres.');
      return;
    }

    setChangingPassword(true);
    try {
      const response = await api.post(API_ENDPOINTS.changePassword, { senha_atual: senhaAtual, nova_senha: novaSenha });
      const data = response.data;

      // Update stored token
      if (data.token) {
        await setAuthToken(data.token);
      }

      Alert.alert('Sucesso', 'Senha alterada com sucesso.');
      setShowPasswordForm(false);
      setSenhaAtual('');
      setNovaSenha('');
      setConfirmaSenha('');
    } catch (error) {
      Alert.alert('Erro', error?.message || 'Falha de rede ao alterar senha.');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleLogout = async () => {
    Alert.alert('Sair', 'Deseja realmente sair?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Sair',
        style: 'destructive',
        onPress: async () => {
          await authService.logout();
          navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1B9E5A" />
        <Text style={styles.loadingText}>Carregando perfil...</Text>
      </View>
    );
  }

  const displayName = profile?.nome || profile?.first_name || profile?.username || 'Usuário';
  const email = profile?.email || '';
  const username = profile?.username || '';
  const dateJoined = profile?.date_joined ? new Date(profile.date_joined).toLocaleDateString('pt-BR') : '';
  const pontosCadastrados = profile?.pontos_cadastrados ?? profile?.pontos ?? 0;
  const badgesCount = profile?.badges_count ?? (Array.isArray(profile?.badges) ? profile.badges.length : 0);
  const pontuacao = profile?.pontuacao ?? profile?.score ?? 0;
  const nivel = profile?.nivel || '';

  return (
    <ScrollView style={styles.scrollView} contentContainerStyle={{ paddingBottom: Math.max(24, insets.bottom + 16) }}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={40} color="#fff" />
          </View>
          {!!nivel && (
            <View style={styles.nivelBadge}>
              <Text style={styles.nivelText}>{nivel}</Text>
            </View>
          )}
        </View>
        <Text style={styles.displayName}>{displayName}</Text>
        {!!username && <Text style={styles.username}>@{username}</Text>}
        {!!email && <Text style={styles.email}>{email}</Text>}
        {!!dateJoined && <Text style={styles.dateJoined}>Membro desde {dateJoined}</Text>}

        {errorMessage && (
          <View style={styles.errorCard}>
            <Ionicons name="warning-outline" size={16} color="#DC2626" />
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        )}
      </View>

      {/* Stats */}
      <View style={styles.statsRow}>
        <StatCard icon="map" color="#0EA5E9" value={pontosCadastrados} label="PANCs" />
        <StatCard icon="medal" color="#D97706" value={badgesCount} label="Badges" />
        <StatCard icon="star" color="#8B5CF6" value={pontuacao} label="Pontos" />
      </View>

      {/* User Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Informações</Text>
        <View style={styles.infoCard}>
          <InfoRow icon="person-outline" label="Nome" value={displayName} />
          <InfoRow icon="at-outline" label="Usuário" value={username} />
          <InfoRow icon="mail-outline" label="Email" value={email} />
          <InfoRow icon="calendar-outline" label="Membro desde" value={dateJoined} />
        </View>
      </View>

      {/* Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Ações</Text>

        <TouchableOpacity style={styles.actionBtn} onPress={() => navigation.navigate('EditarPerfil')}>
          <Ionicons name="create-outline" size={20} color="#1B9E5A" />
          <Text style={styles.actionBtnText}>Editar Perfil</Text>
          <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionBtn} onPress={() => setShowPasswordForm(!showPasswordForm)}>
          <Ionicons name="lock-closed-outline" size={20} color="#D97706" />
          <Text style={styles.actionBtnText}>Alterar Senha</Text>
          <Ionicons name={showPasswordForm ? 'chevron-up' : 'chevron-forward'} size={18} color="#CBD5E1" />
        </TouchableOpacity>

        {/* Password Change Form */}
        {showPasswordForm && (
          <View style={styles.passwordForm}>
            <TextInput
              style={styles.passwordInput}
              placeholder="Senha atual"
              placeholderTextColor="#94A3B8"
              secureTextEntry
              value={senhaAtual}
              onChangeText={setSenhaAtual}
            />
            <TextInput
              style={styles.passwordInput}
              placeholder="Nova senha"
              placeholderTextColor="#94A3B8"
              secureTextEntry
              value={novaSenha}
              onChangeText={setNovaSenha}
            />
            <TextInput
              style={styles.passwordInput}
              placeholder="Confirmar nova senha"
              placeholderTextColor="#94A3B8"
              secureTextEntry
              value={confirmaSenha}
              onChangeText={setConfirmaSenha}
            />
            <TouchableOpacity
              style={[styles.passwordSubmitBtn, changingPassword && { opacity: 0.6 }]}
              onPress={handleChangePassword}
              disabled={changingPassword}
            >
              {changingPassword ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.passwordSubmitText}>Alterar Senha</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        <TouchableOpacity style={[styles.actionBtn, styles.logoutBtn]} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={20} color="#DC2626" />
          <Text style={[styles.actionBtnText, { color: '#DC2626' }]}>Sair da Conta</Text>
          <Ionicons name="chevron-forward" size={18} color="#CBD5E1" />
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: { flex: 1, backgroundColor: '#F8FAFC' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC' },
  loadingText: { marginTop: 12, color: '#64748B' },

  header: { backgroundColor: '#1B9E5A', paddingVertical: 32, paddingHorizontal: 20, alignItems: 'center' },
  avatarContainer: { position: 'relative', marginBottom: 12 },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center', borderWidth: 3, borderColor: 'rgba(255,255,255,0.4)' },
  nivelBadge: { position: 'absolute', bottom: -4, right: -8, backgroundColor: '#D97706', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10 },
  nivelText: { color: '#fff', fontSize: 10, fontWeight: '800' },
  displayName: { fontSize: 24, fontWeight: '800', color: '#fff' },
  username: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 2 },
  email: { fontSize: 14, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  dateJoined: { fontSize: 12, color: 'rgba(255,255,255,0.6)', marginTop: 4 },
  errorCard: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 12, padding: 10, backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 10 },
  errorText: { color: '#FEE2E2', fontSize: 13, flex: 1 },

  statsRow: { flexDirection: 'row', gap: 12, paddingHorizontal: 16, marginTop: -20 },
  statCard: { flex: 1, backgroundColor: '#fff', borderRadius: 16, padding: 16, alignItems: 'center', borderWidth: 1, borderColor: '#F1F5F9', shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2 },
  statIconBg: { width: 44, height: 44, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  statValue: { fontSize: 22, fontWeight: '800', color: '#0F172A' },
  statLabel: { fontSize: 11, color: '#94A3B8', fontWeight: '600', marginTop: 2 },

  section: { marginTop: 24, paddingHorizontal: 16 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#0F172A', marginBottom: 12 },

  infoCard: { backgroundColor: '#fff', borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: '#F1F5F9' },
  infoRow: { flexDirection: 'row', alignItems: 'center', padding: 14, borderBottomWidth: 1, borderBottomColor: '#F8FAFC' },
  infoIconBg: { width: 36, height: 36, borderRadius: 10, backgroundColor: '#F8FAFC', justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  infoContent: { flex: 1 },
  infoLabel: { fontSize: 12, color: '#94A3B8', marginBottom: 2 },
  infoValue: { fontSize: 15, color: '#0F172A', fontWeight: '600' },

  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#F1F5F9',
    gap: 12,
  },
  actionBtnText: { flex: 1, fontSize: 15, fontWeight: '600', color: '#0F172A' },
  logoutBtn: { marginTop: 8 },

  passwordForm: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#FDE68A',
    gap: 10,
  },
  passwordInput: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 12,
    fontSize: 15,
    color: '#0F172A',
  },
  passwordSubmitBtn: {
    backgroundColor: '#D97706',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  passwordSubmitText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
