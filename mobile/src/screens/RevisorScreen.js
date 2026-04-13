import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator, TextInput, Alert, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { API_ENDPOINTS } from '../config/api';
import api from '../services/apiClient';

export default function RevisorScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [loading, setLoading] = useState(true);
  const [pontosPendentes, setPontosPendentes] = useState([]);
  const [filtroColaborador, setFiltroColaborador] = useState('');
  const [filtroNome, setFiltroNome] = useState('');
  const [filtroCidade, setFiltroCidade] = useState('');
  const [showFiltros, setShowFiltros] = useState(false);
  const [enviandoParecerId, setEnviandoParecerId] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    let ativo = true;
    fetchPontosPendentes(ativo);
    return () => { ativo = false; };
  }, []);

  const fetchPontosPendentes = async (ativo) => {
    setLoading(true);
    setErrorMessage(null);

    try {
      let data;
      try {
        const response = await api.get(API_ENDPOINTS.pontosRevisaoCientifica);
        data = response.data;
      } catch (error) {
        if (error.status === 401 || error.status === 403) {
          const fallback = await api.get(API_ENDPOINTS.pontos, { params: { status_fluxo: 'submetido' } });
          data = fallback.data;
        } else {
          throw error;
        }
      }

      const lista = Array.isArray(data) ? data : data?.results || data?.data || [];
      if (ativo) setPontosPendentes(Array.isArray(lista) ? lista : []);
    } catch (error) {
      console.error('Erro ao buscar pontos pendentes:', error);
      if (ativo) {
        setErrorMessage('Falha ao carregar pontos pendentes. Verifique sua conexão.');
        setPontosPendentes([]);
      }
    } finally {
      if (ativo) setLoading(false);
    }
  };

  const getConfiancaInfo = (score) => {
    const confianca = Number(score || 0);
    if (confianca >= 85) return { label: 'Alta', color: '#16A34A', bg: '#DCFCE7', icon: 'shield-checkmark' };
    if (confianca >= 60) return { label: 'Média', color: '#D97706', bg: '#FEF3C7', icon: 'shield-half' };
    return { label: 'Baixa', color: '#DC2626', bg: '#FEE2E2', icon: 'shield-outline' };
  };

  const filtrarPontos = () => pontosPendentes.filter((item) => {
    const colaborador = (item.colaborador || '').toLowerCase();
    const nome = (item.nome_popular || '').toLowerCase();
    const cidade = (item.cidade || '').toLowerCase();
    const filtroCol = filtroColaborador.trim().toLowerCase();
    const filtroNom = filtroNome.trim().toLowerCase();
    const filtroCid = filtroCidade.trim().toLowerCase();

    if (filtroCol && !colaborador.includes(filtroCol)) return false;
    if (filtroNom && !nome.includes(filtroNom)) return false;
    if (filtroCid && !cidade.includes(filtroCid)) return false;
    return true;
  });

  const enviarParecer = async (item, decisaoFinal) => {
    const labelDecisao = decisaoFinal === 'validado' ? 'aprovar' : decisaoFinal === 'rejeitado' ? 'reprovar' : 'solicitar revisão';

    Alert.alert(
      `Confirmar: ${labelDecisao}`,
      `Deseja ${labelDecisao} "${item.nome_popular || 'este ponto'}"?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Confirmar',
          onPress: async () => {
            try {
              setEnviandoParecerId(item.id);
              await api.post(API_ENDPOINTS.validarPontoCientifico(item.id), {
                decisao_final: decisaoFinal,
                observacao: '',
                especie_final: item.nome_cientifico || item.nome_popular || '',
              });
              await fetchPontosPendentes(true);
            } catch (error) {
              Alert.alert('Erro ao validar', error?.message || 'Falha ao enviar parecer.');
            } finally {
              setEnviandoParecerId(null);
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1B9E5A" />
        <Text style={styles.loadingText}>Carregando pontos...</Text>
      </View>
    );
  }

  const pontosFiltrados = filtrarPontos();
  const temFiltrosAtivos = filtroColaborador || filtroNome || filtroCidade;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: 16 }]}>
        <View style={styles.headerTop}>
          <Ionicons name="shield-checkmark" size={28} color="#1B9E5A" />
          <View style={styles.headerInfo}>
            <Text style={styles.title}>Painel do Revisor</Text>
            <Text style={styles.subtitle}>{pontosFiltrados.length} ponto{pontosFiltrados.length !== 1 ? 's' : ''} em revisão</Text>
          </View>
          <TouchableOpacity
            style={[styles.filterToggle, showFiltros && styles.filterToggleActive]}
            onPress={() => setShowFiltros(!showFiltros)}
          >
            <Ionicons name="filter" size={20} color={showFiltros ? '#fff' : '#64748B'} />
            {temFiltrosAtivos && <View style={styles.filterDot} />}
          </TouchableOpacity>
        </View>

        {errorMessage && (
          <View style={styles.errorCard}>
            <Ionicons name="warning-outline" size={16} color="#DC2626" />
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        )}
      </View>

      {/* Filtros */}
      {showFiltros && (
        <View style={styles.filtrosContainer}>
          <TextInput style={styles.filtroInput} placeholder="Filtrar por colaborador" placeholderTextColor="#94A3B8" value={filtroColaborador} onChangeText={setFiltroColaborador} />
          <TextInput style={styles.filtroInput} placeholder="Filtrar por nome popular" placeholderTextColor="#94A3B8" value={filtroNome} onChangeText={setFiltroNome} />
          <TextInput style={styles.filtroInput} placeholder="Filtrar por cidade" placeholderTextColor="#94A3B8" value={filtroCidade} onChangeText={setFiltroCidade} />
          {temFiltrosAtivos && (
            <TouchableOpacity
              style={styles.clearFilters}
              onPress={() => { setFiltroColaborador(''); setFiltroNome(''); setFiltroCidade(''); }}
            >
              <Ionicons name="close-circle" size={16} color="#DC2626" />
              <Text style={styles.clearFiltersText}>Limpar filtros</Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {pontosFiltrados.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="checkmark-circle" size={64} color="#CBD5E1" />
          <Text style={styles.emptyTitle}>Tudo revisado!</Text>
          <Text style={styles.emptyText}>Nenhum ponto pendente de validação.</Text>
          <TouchableOpacity style={styles.refreshBtn} onPress={() => fetchPontosPendentes(true)}>
            <Ionicons name="refresh" size={18} color="#1B9E5A" />
            <Text style={styles.refreshBtnText}>Atualizar</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={pontosFiltrados}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={{ padding: 12, paddingBottom: 20 + insets.bottom }}
          renderItem={({ item }) => {
            const confiancaInfo = getConfiancaInfo(item.score_identificacao);
            const comestivel = item.comestivel || !!item.parte_comestivel;

            return (
              <View style={styles.card}>
                <TouchableOpacity
                  style={styles.cardContent}
                  onPress={() => navigation.navigate('DetalhePonto', { id: item.id })}
                  activeOpacity={0.7}
                >
                  {/* Foto miniatura */}
                  {item.foto_url ? (
                    <Image source={{ uri: item.foto_url }} style={styles.cardThumb} />
                  ) : (
                    <View style={[styles.cardThumb, styles.cardThumbPlaceholder]}>
                      <Ionicons name="leaf" size={24} color="#BBF7D0" />
                    </View>
                  )}

                  <View style={styles.cardBody}>
                    <View style={styles.cardTitleRow}>
                      <Text style={styles.cardTitle} numberOfLines={1}>{item.nome_popular || 'Sem identificação'}</Text>
                      <View style={[styles.confiancaBadge, { backgroundColor: confiancaInfo.bg }]}>
                        <Ionicons name={confiancaInfo.icon} size={12} color={confiancaInfo.color} />
                        <Text style={[styles.confiancaText, { color: confiancaInfo.color }]}>{confiancaInfo.label}</Text>
                      </View>
                    </View>

                    <Text style={styles.cardSubtitle} numberOfLines={1}>{item.nome_cientifico || 'Nome científico pendente'}</Text>

                    {/* Plant info inline */}
                    <View style={styles.cardInfoRow}>
                      <Ionicons name="location-outline" size={13} color="#94A3B8" />
                      <Text style={styles.cardInfoText}>{item.cidade || '-'} / {item.estado || '-'}</Text>
                    </View>
                    <View style={styles.cardInfoRow}>
                      <Ionicons name="person-outline" size={13} color="#94A3B8" />
                      <Text style={styles.cardInfoText}>{item.colaborador || 'Desconhecido'}</Text>
                    </View>

                    {/* Edibility & season info */}
                    <View style={styles.cardTagsRow}>
                      {comestivel && (
                        <View style={styles.cardTag}>
                          <Ionicons name="checkmark-circle" size={12} color="#16A34A" />
                          <Text style={[styles.cardTagText, { color: '#16A34A' }]}>Comestível</Text>
                        </View>
                      )}
                      {!!item.parte_comestivel && (
                        <View style={styles.cardTag}>
                          <Ionicons name="leaf-outline" size={12} color="#0EA5E9" />
                          <Text style={styles.cardTagText}>{item.parte_comestivel}</Text>
                        </View>
                      )}
                      {!!item.epoca_frutificacao && (
                        <View style={styles.cardTag}>
                          <Ionicons name="flower-outline" size={12} color="#D97706" />
                          <Text style={styles.cardTagText}>{item.epoca_frutificacao}</Text>
                        </View>
                      )}
                      {!!item.epoca_colheita && (
                        <View style={styles.cardTag}>
                          <Ionicons name="calendar-outline" size={12} color="#7C3AED" />
                          <Text style={styles.cardTagText}>{item.epoca_colheita}</Text>
                        </View>
                      )}
                    </View>
                  </View>
                </TouchableOpacity>

                {/* Actions */}
                <View style={styles.actionsRow}>
                  <TouchableOpacity
                    style={[styles.actionBtn, styles.aprovarBtn]}
                    disabled={enviandoParecerId === item.id}
                    onPress={() => enviarParecer(item, 'validado')}
                  >
                    <Ionicons name="checkmark-circle" size={18} color="#fff" />
                    <Text style={styles.actionBtnText}>Aprovar</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.actionBtn, styles.pendenciaBtn]}
                    disabled={enviandoParecerId === item.id}
                    onPress={() => enviarParecer(item, 'necessita_revisao')}
                  >
                    <Ionicons name="alert-circle" size={18} color="#fff" />
                    <Text style={styles.actionBtnText}>Pendência</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.actionBtn, styles.reprovarBtn]}
                    disabled={enviandoParecerId === item.id}
                    onPress={() => enviarParecer(item, 'rejeitado')}
                  >
                    <Ionicons name="close-circle" size={18} color="#fff" />
                    <Text style={styles.actionBtnText}>Reprovar</Text>
                  </TouchableOpacity>
                </View>
                {enviandoParecerId === item.id && <ActivityIndicator size="small" color="#1B9E5A" style={{ marginTop: 8 }} />}
              </View>
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC' },
  loadingText: { marginTop: 12, color: '#64748B', fontSize: 15 },

  header: { backgroundColor: '#fff', padding: 16, borderBottomWidth: 1, borderBottomColor: '#F1F5F9' },
  headerTop: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerInfo: { flex: 1 },
  title: { fontSize: 22, fontWeight: '800', color: '#0F172A' },
  subtitle: { fontSize: 13, color: '#64748B', marginTop: 2 },
  filterToggle: { width: 40, height: 40, borderRadius: 12, backgroundColor: '#F1F5F9', justifyContent: 'center', alignItems: 'center' },
  filterToggleActive: { backgroundColor: '#1B9E5A' },
  filterDot: { position: 'absolute', top: 6, right: 6, width: 8, height: 8, borderRadius: 4, backgroundColor: '#DC2626' },
  errorCard: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 10, padding: 10, backgroundColor: '#FEF2F2', borderRadius: 10 },
  errorText: { fontSize: 13, color: '#DC2626', flex: 1 },

  filtrosContainer: { backgroundColor: '#fff', paddingHorizontal: 16, paddingVertical: 10, gap: 8, borderBottomWidth: 1, borderBottomColor: '#F1F5F9' },
  filtroInput: { backgroundColor: '#F8FAFC', borderColor: '#E2E8F0', borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 14, color: '#0F172A' },
  clearFilters: { flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-end' },
  clearFiltersText: { color: '#DC2626', fontSize: 13, fontWeight: '600' },

  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  emptyTitle: { fontSize: 20, fontWeight: '700', color: '#0F172A', marginTop: 16 },
  emptyText: { fontSize: 15, color: '#94A3B8', marginTop: 4 },
  refreshBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 20, paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#F0FDF4', borderRadius: 10, borderWidth: 1, borderColor: '#BBF7D0' },
  refreshBtnText: { color: '#1B9E5A', fontWeight: '700' },

  card: { backgroundColor: '#fff', marginBottom: 10, borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: '#F1F5F9', shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 3, elevation: 1 },
  cardContent: { flexDirection: 'row', padding: 14 },
  cardThumb: { width: 60, height: 60, borderRadius: 12, backgroundColor: '#F1F5F9', marginRight: 12 },
  cardThumbPlaceholder: { justifyContent: 'center', alignItems: 'center', backgroundColor: '#F0FDF4' },
  cardBody: { flex: 1 },
  cardTitleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  cardTitle: { fontSize: 16, fontWeight: '700', color: '#0F172A', flex: 1, marginRight: 8 },
  cardSubtitle: { fontSize: 13, color: '#94A3B8', fontStyle: 'italic', marginTop: 2 },
  cardInfoRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  cardInfoText: { fontSize: 12, color: '#64748B' },
  cardTagsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  cardTag: { flexDirection: 'row', alignItems: 'center', gap: 3, backgroundColor: '#F8FAFC', paddingHorizontal: 6, paddingVertical: 3, borderRadius: 6 },
  cardTagText: { fontSize: 11, color: '#64748B', fontWeight: '600' },

  confiancaBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  confiancaText: { fontSize: 11, fontWeight: '700' },

  actionsRow: { flexDirection: 'row', gap: 8, paddingHorizontal: 14, paddingBottom: 14 },
  actionBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4, paddingVertical: 10, borderRadius: 10 },
  aprovarBtn: { backgroundColor: '#16A34A' },
  pendenciaBtn: { backgroundColor: '#D97706' },
  reprovarBtn: { backgroundColor: '#DC2626' },
  actionBtnText: { color: '#fff', fontWeight: '700', fontSize: 12 },
});
