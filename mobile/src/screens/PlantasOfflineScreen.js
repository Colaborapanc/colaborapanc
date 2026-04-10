/**
 * Tela de gerenciamento de plantas offline
 * Permite selecionar e baixar plantas específicas para uso offline
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import plantasOfflineService from '../services/plantasOfflineService';
import speciesFocusService from '../services/speciesFocusService';

const PlantasOfflineScreen = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const [plantas, setPlantas] = useState([]);
  const [plantasSelecionadas, setPlantasSelecionadas] = useState([]);
  const [pacotes, setPacotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busca, setBusca] = useState('');
  const [filtros, setFiltros] = useState({});
  const [modoSelecao, setModoSelecao] = useState(false);
  const [estatisticas, setEstatisticas] = useState(null);
  const [tabAtiva, setTabAtiva] = useState('plantas');
  const [expandedPlantId, setExpandedPlantId] = useState(null);
  const [statusBaseOffline, setStatusBaseOffline] = useState({ status: 'nao_baixada', quantidade: 0, tamanho_estimado_mb: 0 });

  const chaveVisualItem = (item, index = 0) => {
    const candidatos = [
      item?.stable_id,
      item?.id,
      item?.plataforma_id,
      item?.nome_cientifico,
      item?.nome_popular,
    ];
    for (const candidato of candidatos) {
      if (candidato !== null && candidato !== undefined && String(candidato).trim() !== '') {
        return String(candidato);
      }
    }
    return `fallback-${index}`;
  };

  const normalizarParaLista = (itens = [], fontePadrao = 'ui') => {
    const normalizados = speciesFocusService.normalizarListaParaUI(itens, { fontePadrao });
    return normalizados.filter((item, index) => String(chaveVisualItem(item, index)).trim() !== '');
  };

  useEffect(() => {
    carregarDados();
    carregarEstatisticas();
    carregarStatusBase();
  }, []);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const resultadoPlantas = await plantasOfflineService.listarPlantasDisponiveis(filtros);
      if (resultadoPlantas.sucesso) {
        setPlantas(normalizarParaLista(resultadoPlantas.plantas, 'listagem_padrao'));
      } else if (!resultadoPlantas.offline) {
        Alert.alert('Erro', resultadoPlantas.erro);
      }
      const resultadoPacotes = await plantasOfflineService.listarPacotes();
      if (resultadoPacotes.sucesso) {
        setPacotes(resultadoPacotes.pacotes);
      }
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      Alert.alert('Erro', 'Erro ao carregar dados');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const buscarEspeciesReferenciais = async () => {
    const termoBusca = String(busca || '').trim();
    if (termoBusca.length === 0) {
      await carregarDados();
      return;
    }

    try {
      setLoading(true);
      const resultadoBusca = await speciesFocusService.buscarEspeciesRecursivamente({
        busca: termoBusca,
        filtros,
      });
      setPlantas(normalizarParaLista(resultadoBusca.especies || [], resultadoBusca?.fonte_resultado || 'busca_recursiva'));
    } catch (error) {
      console.error('Erro na busca referencial:', error);
      Alert.alert('Erro', 'Não foi possível buscar espécies referenciais');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const carregarEstatisticas = async () => {
    try {
      const stats = await plantasOfflineService.obterEstatisticas();
      setEstatisticas(stats);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const carregarStatusBase = async () => {
    try {
      const status = await speciesFocusService.obterStatusBaseOffline();
      setStatusBaseOffline(status || { status: 'nao_baixada', quantidade: 0, tamanho_estimado_mb: 0 });
    } catch (error) {
      console.warn('Falha ao carregar status da base offline:', error?.message || error);
      setStatusBaseOffline({ status: 'nao_baixada', quantidade: 0, tamanho_estimado_mb: 0 });
    }
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (String(busca || '').trim().length > 0) {
        buscarEspeciesReferenciais();
      } else {
        carregarDados();
      }
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [busca]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    if (String(busca || '').trim().length > 0) {
      buscarEspeciesReferenciais();
    } else {
      carregarDados();
    }
    carregarEstatisticas();
    carregarStatusBase();
  }, [busca]);

  const toggleSelecaoPlanta = (plantaId) => {
    setPlantasSelecionadas(prev => {
      if (prev.includes(plantaId)) {
        return prev.filter(id => id !== plantaId);
      }
      return [...prev, plantaId];
    });
  };

  const selecionarTodas = () => {
    setPlantasSelecionadas(plantas.map((p, index) => chaveVisualItem(p, index)));
  };

  const limparSelecao = () => {
    setPlantasSelecionadas([]);
    setModoSelecao(false);
  };

  const baixarPlantasSelecionadas = async () => {
    if (plantasSelecionadas.length === 0) {
      Alert.alert('Atenção', 'Selecione pelo menos uma planta');
      return;
    }

    const tamanhoTotal = plantas
      .filter((p, index) => plantasSelecionadas.includes(chaveVisualItem(p, index)))
      .reduce((sum, p) => sum + p.tamanho_estimado_mb, 0);

    Alert.alert(
      'Confirmar Download',
      `Deseja baixar ${plantasSelecionadas.length} plantas?\nTamanho estimado: ${tamanhoTotal.toFixed(1)} MB`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Baixar',
          onPress: async () => {
            try {
              setLoading(true);
              const especiesDisponiveis = plantas.map((p) => ({ ...p }));
              const resultado = await speciesFocusService.baixarBaseSelecionada({
                ids: plantasSelecionadas,
                especiesDisponiveis,
                configuracao: { limiar_confianca_padrao: 0.65 },
              });
              Alert.alert('Sucesso', `${resultado.plantasBaixadas} de ${resultado.total} plantas baixadas!`);
              limparSelecao();
              carregarDados();
              carregarEstatisticas();
              carregarStatusBase();
            } catch (error) {
              Alert.alert('Erro', 'Erro ao baixar plantas');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  const baixarPacote = async (pacoteId, nome) => {
    Alert.alert(
      'Confirmar Download',
      `Deseja baixar o pacote "${nome}"?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Baixar',
          onPress: async () => {
            try {
              setLoading(true);
              const resultado = await plantasOfflineService.baixarPacote(pacoteId);
              if (resultado.sucesso) {
                Alert.alert('Sucesso', resultado.mensagem);
                carregarDados();
                carregarEstatisticas();
              } else {
                Alert.alert('Erro', resultado.erro);
              }
            } catch (error) {
              Alert.alert('Erro', 'Erro ao baixar pacote');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  const baixarBaseReferencialIntegrada = async () => {
    try {
      setLoading(true);
      const sync = await plantasOfflineService.sincronizarBaseIntegracao({ limite: 120 });
      if (!sync?.sucesso) {
        Alert.alert('Falha no download', sync?.erro || 'Não foi possível baixar a base integrada.');
        return;
      }
      Alert.alert('Base offline atualizada', `${sync.plantasSincronizadas} espécies referenciais sincronizadas.`);
      carregarDados();
      carregarEstatisticas();
      carregarStatusBase();
    } catch (error) {
      Alert.alert('Erro', 'Falha ao sincronizar base referencial offline.');
    } finally {
      setLoading(false);
    }
  };

  const renderPlantaItem = ({ item }) => {
    const itemKey = chaveVisualItem(item);
    const selecionada = plantasSelecionadas.includes(itemKey);
    const jaBaixada = item.ja_baixada;
    const isExpanded = expandedPlantId === itemKey;
    const comestivel = !!item.parte_comestivel;

    return (
      <TouchableOpacity
        style={[
          styles.plantaItem,
          selecionada && styles.plantaItemSelecionada,
          jaBaixada && styles.plantaItemBaixada,
        ]}
        onPress={() => {
          if (modoSelecao) {
            toggleSelecaoPlanta(itemKey);
          } else {
            setExpandedPlantId(isExpanded ? null : itemKey);
          }
        }}
        onLongPress={() => {
          setModoSelecao(true);
          toggleSelecaoPlanta(itemKey);
        }}
        activeOpacity={0.7}
      >
        <View style={styles.plantaMainRow}>
          <View style={styles.plantaInfo}>
            <View style={styles.plantaNameRow}>
              <Text style={styles.plantaNome}>{item.nome_popular}</Text>
              {jaBaixada && <Ionicons name="checkmark-circle" size={18} color="#16A34A" />}
            </View>
            <Text style={styles.plantaCientifico}>{item.nome_cientifico}</Text>

            {/* Tags inline */}
            <View style={styles.plantaTags}>
              {comestivel && (
                <View style={[styles.tag, styles.tagComestivel]}>
                  <Ionicons name="checkmark-circle" size={11} color="#16A34A" />
                  <Text style={[styles.tagText, { color: '#16A34A' }]}>Comestível</Text>
                </View>
              )}
              {item.bioma && (
                <View style={styles.tag}>
                  <Text style={styles.tagText}>{item.bioma}</Text>
                </View>
              )}
              {item.fonte_resultado && (
                <View style={styles.tag}>
                  <Text style={styles.tagText}>
                    {item.fonte_resultado === 'offline_referencial' ? 'Cache offline' : 'Integração online'}
                  </Text>
                </View>
              )}
              {item.tem_modelo_ar && (
                <View style={[styles.tag, styles.tagAR]}>
                  <Text style={[styles.tagText, { color: '#1D4ED8' }]}>AR</Text>
                </View>
              )}
              {item.num_variacoes > 0 && (
                <View style={[styles.tag, styles.tagVariacoes]}>
                  <Text style={[styles.tagText, { color: '#D97706' }]}>{item.num_variacoes} var.</Text>
                </View>
              )}
            </View>
          </View>

          <View style={styles.plantaRight}>
            {modoSelecao && (
              <Ionicons
                name={selecionada ? 'checkbox' : 'square-outline'}
                size={24}
                color={selecionada ? '#1B9E5A' : '#CBD5E1'}
              />
            )}
            <Ionicons name={isExpanded ? 'chevron-up' : 'chevron-down'} size={18} color="#94A3B8" />
          </View>
        </View>

        {/* Detalhes expandidos */}
        {isExpanded && (
          <View style={styles.expandedDetails}>
            <View style={styles.expandedDivider} />

            {/* Comestibilidade */}
            <View style={styles.expandedSection}>
              <View style={styles.expandedRow}>
                <Ionicons name={comestivel ? 'checkmark-circle' : 'help-circle-outline'} size={18} color={comestivel ? '#16A34A' : '#94A3B8'} />
                <Text style={[styles.expandedLabel, { color: comestivel ? '#16A34A' : '#64748B' }]}>
                  {comestivel ? 'Planta Comestível' : 'Comestibilidade não informada'}
                </Text>
              </View>
              {!!item.parte_comestivel && (
                <View style={styles.expandedRow}>
                  <Ionicons name="leaf-outline" size={16} color="#16A34A" />
                  <Text style={styles.expandedText}>Parte comestível: <Text style={styles.expandedBold}>{item.parte_comestivel}</Text></Text>
                </View>
              )}
              {!!item.forma_uso && (
                <View style={styles.expandedRow}>
                  <Ionicons name="restaurant-outline" size={16} color="#0EA5E9" />
                  <Text style={styles.expandedText}>Uso: <Text style={styles.expandedBold}>{item.forma_uso}</Text></Text>
                </View>
              )}
            </View>

            {/* Época */}
            {(!!item.epoca_frutificacao || !!item.epoca_colheita) && (
              <View style={styles.expandedEpocaRow}>
                {!!item.epoca_frutificacao && (
                  <View style={styles.expandedEpocaCard}>
                    <Ionicons name="flower-outline" size={18} color="#D97706" />
                    <Text style={styles.expandedEpocaLabel}>Frutificação</Text>
                    <Text style={styles.expandedEpocaValue}>{item.epoca_frutificacao}</Text>
                  </View>
                )}
                {!!item.epoca_colheita && (
                  <View style={styles.expandedEpocaCard}>
                    <Ionicons name="basket-outline" size={18} color="#7C3AED" />
                    <Text style={styles.expandedEpocaLabel}>Colheita</Text>
                    <Text style={styles.expandedEpocaValue}>{item.epoca_colheita}</Text>
                  </View>
                )}
              </View>
            )}

            {/* Info adicional */}
            <View style={styles.expandedFooter}>
              {!!item.grupo_taxonomico && (
                <View style={styles.expandedRow}>
                  <Ionicons name="git-branch-outline" size={14} color="#94A3B8" />
                  <Text style={styles.expandedMeta}>{item.grupo_taxonomico}</Text>
                </View>
              )}
              {!!item.regiao_ocorrencia && (
                <View style={styles.expandedRow}>
                  <Ionicons name="map-outline" size={14} color="#94A3B8" />
                  <Text style={styles.expandedMeta}>{item.regiao_ocorrencia}</Text>
                </View>
              )}
              <View style={styles.expandedRow}>
                <Ionicons name="cloud-download-outline" size={14} color="#94A3B8" />
                <Text style={styles.expandedMeta}>{(item.tamanho_estimado_mb || 0).toFixed(1)} MB</Text>
              </View>
            </View>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderPacoteItem = ({ item }) => {
    const progresso = item.total_plantas > 0
      ? (item.plantas_baixadas / item.total_plantas) * 100
      : 0;

    return (
      <TouchableOpacity
        style={[styles.pacoteItem, item.completo && styles.pacoteCompleto]}
        onPress={() => baixarPacote(item.id, item.nome)}
        activeOpacity={0.7}
      >
        <View style={styles.pacoteHeader}>
          <Text style={styles.pacoteNome}>{item.nome}</Text>
          <Text style={styles.pacoteTamanho}>{item.tamanho_estimado_mb} MB</Text>
        </View>

        <Text style={styles.pacoteDescricao} numberOfLines={2}>{item.descricao}</Text>

        <View style={styles.pacoteInfo}>
          <View style={styles.pacoteTag}>
            <Ionicons name="leaf" size={13} color="#16A34A" />
            <Text style={styles.pacoteTagText}>{item.total_plantas} plantas</Text>
          </View>
          {item.bioma && (
            <View style={styles.pacoteTag}>
              <Ionicons name="earth" size={13} color="#0EA5E9" />
              <Text style={styles.pacoteTagText}>{item.bioma}</Text>
            </View>
          )}
          <View style={styles.pacoteTag}>
            <Ionicons name="star" size={13} color="#D97706" />
            <Text style={styles.pacoteTagText}>{item.dificuldade}</Text>
          </View>
        </View>

        {progresso > 0 && (
          <View style={styles.progressoContainer}>
            <View style={styles.progressoBarra}>
              <View style={[styles.progressoPreenchido, { width: `${progresso}%` }]} />
            </View>
            <Text style={styles.progressoTexto}>{item.plantas_baixadas}/{item.total_plantas}</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderHeader = () => (
    <View style={styles.header}>
      {estatisticas && (
        <View style={styles.estatisticas}>
          <View style={styles.estatItem}>
            <Ionicons name="leaf" size={20} color="#1B9E5A" />
            <Text style={styles.estatValor}>{estatisticas.totalPlantas}</Text>
            <Text style={styles.estatLabel}>Plantas</Text>
          </View>
          <View style={styles.estatDivider} />
          <View style={styles.estatItem}>
            <Ionicons name="cloud-download" size={20} color="#0EA5E9" />
            <Text style={styles.estatValor}>{estatisticas.tamanhoTotalMb.toFixed(1)} MB</Text>
            <Text style={styles.estatLabel}>Usado</Text>
          </View>
          <View style={styles.estatDivider} />
          <View style={styles.estatItem}>
            <Ionicons name="pie-chart" size={20} color="#D97706" />
            <Text style={styles.estatValor}>{estatisticas.percentualUsado}%</Text>
            <Text style={styles.estatLabel}>Capacidade</Text>
          </View>
        </View>
      )}

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, tabAtiva === 'plantas' && styles.tabAtiva]}
          onPress={() => setTabAtiva('plantas')}
        >
          <Ionicons name="leaf-outline" size={18} color={tabAtiva === 'plantas' ? '#1B9E5A' : '#94A3B8'} />
          <Text style={[styles.tabTexto, tabAtiva === 'plantas' && styles.tabTextoAtiva]}>Plantas</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, tabAtiva === 'pacotes' && styles.tabAtiva]}
          onPress={() => setTabAtiva('pacotes')}
        >
          <Ionicons name="cube-outline" size={18} color={tabAtiva === 'pacotes' ? '#1B9E5A' : '#94A3B8'} />
          <Text style={[styles.tabTexto, tabAtiva === 'pacotes' && styles.tabTextoAtiva]}>Pacotes</Text>
        </TouchableOpacity>
      </View>

      {/* Barra de busca */}
      {tabAtiva === 'plantas' && (
        <View style={styles.buscaContainer}>
          <Ionicons name="search" size={18} color="#94A3B8" />
          <TextInput
            style={styles.buscaInput}
            placeholder="Buscar por nome popular, científico ou sinônimo..."
            placeholderTextColor="#94A3B8"
            value={busca}
            onChangeText={setBusca}
          />
          {busca.length > 0 && (
            <TouchableOpacity onPress={() => setBusca('')}>
              <Ionicons name="close-circle" size={18} color="#94A3B8" />
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );

  const renderBarraAcoes = () => {
    if (!modoSelecao) return null;

    return (
      <View style={[styles.barraAcoes, { paddingBottom: 10 + insets.bottom }]}>
        <TouchableOpacity style={styles.botaoAcaoCancel} onPress={limparSelecao}>
          <Ionicons name="close" size={20} color="#fff" />
          <Text style={styles.botaoAcaoTexto}>Cancelar</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.botaoAcaoAll} onPress={selecionarTodas}>
          <Ionicons name="checkmark-done" size={20} color="#fff" />
          <Text style={styles.botaoAcaoTexto}>Todas</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.botaoAcaoDownload} onPress={baixarPlantasSelecionadas}>
          <Ionicons name="download" size={20} color="#fff" />
          <Text style={styles.botaoAcaoTexto}>Baixar ({plantasSelecionadas.length})</Text>
        </TouchableOpacity>
      </View>
    );
  };

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1B9E5A" />
        <Text style={styles.loadingText}>Carregando plantas...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {renderHeader()}

      <View style={styles.baseOfflineCard}>
        <View style={styles.baseOfflineRow}>
          <Ionicons name="folder-open" size={20} color="#1B5E20" />
          <View style={styles.baseOfflineInfo}>
            <Text style={styles.baseOfflineTitle}>Base offline direcionada</Text>
            <Text style={styles.baseOfflineText}>
              {statusBaseOffline.status === 'nao_baixada' ? 'Não baixada' : statusBaseOffline.status} | {statusBaseOffline.quantidade || 0} espécies | {Number(statusBaseOffline.tamanho_estimado_mb || 0).toFixed(1)} MB
            </Text>
          </View>
        </View>
        <TouchableOpacity style={styles.baseOfflineAction} onPress={baixarBaseReferencialIntegrada}>
          <Ionicons name="cloud-download-outline" size={16} color="#fff" />
          <Text style={styles.baseOfflineActionText}>Baixar base referencial integrada</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={tabAtiva === 'plantas' ? normalizarParaLista(plantas, 'ui_render') : pacotes}
        renderItem={tabAtiva === 'plantas' ? renderPlantaItem : renderPacoteItem}
        keyExtractor={(item, index) => chaveVisualItem(item, index)}
        contentContainerStyle={[styles.lista, { paddingBottom: 120 + insets.bottom }]}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#1B9E5A']} />}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="leaf-outline" size={56} color="#CBD5E1" />
            <Text style={styles.emptyText}>
              {tabAtiva === 'plantas'
                ? busca.length > 0
                  ? 'Nenhuma espécie encontrada para esta busca'
                  : 'Digite um nome para buscar na base referencial integrada'
                : 'Nenhum pacote disponível'}
            </Text>
            {tabAtiva === 'plantas' && busca.length > 0 && (
              <Text style={styles.emptyHint}>
                Tente buscar por nome popular, científico ou sinônimo
              </Text>
            )}
          </View>
        }
      />

      {renderBarraAcoes()}

      {/* FAB */}
      <TouchableOpacity
        style={[styles.fab, { bottom: 20 + insets.bottom }]}
        onPress={() => navigation.navigate('MinhasPlantas')}
        activeOpacity={0.8}
      >
        <Ionicons name="folder-open" size={24} color="#fff" />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC' },
  loadingText: { marginTop: 12, fontSize: 15, color: '#64748B' },
  header: { backgroundColor: '#fff', paddingBottom: 8, borderBottomWidth: 1, borderBottomColor: '#F1F5F9' },
  baseOfflineCard: { backgroundColor: '#F0FDF4', padding: 12, marginHorizontal: 12, marginTop: 10, borderRadius: 12, borderWidth: 1, borderColor: '#BBF7D0' },
  baseOfflineRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  baseOfflineInfo: { flex: 1 },
  baseOfflineTitle: { fontWeight: '700', color: '#1B5E20', fontSize: 14 },
  baseOfflineText: { color: '#2E7D32', marginTop: 2, fontSize: 12 },
  baseOfflineAction: {
    marginTop: 10,
    backgroundColor: '#1B9E5A',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 6,
  },
  baseOfflineActionText: { color: '#fff', fontWeight: '700', fontSize: 12 },

  estatisticas: { flexDirection: 'row', justifyContent: 'space-around', alignItems: 'center', paddingVertical: 16, paddingHorizontal: 12 },
  estatItem: { alignItems: 'center', gap: 4 },
  estatDivider: { width: 1, height: 40, backgroundColor: '#F1F5F9' },
  estatValor: { fontSize: 18, fontWeight: '800', color: '#0F172A' },
  estatLabel: { fontSize: 11, color: '#94A3B8', fontWeight: '600' },

  tabs: { flexDirection: 'row', paddingHorizontal: 12, gap: 8, marginTop: 4 },
  tab: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 10, borderBottomWidth: 2, borderBottomColor: 'transparent' },
  tabAtiva: { borderBottomColor: '#1B9E5A' },
  tabTexto: { fontSize: 15, color: '#94A3B8', fontWeight: '600' },
  tabTextoAtiva: { color: '#1B9E5A' },

  buscaContainer: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F8FAFC', marginHorizontal: 12, marginTop: 8, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12, borderWidth: 1, borderColor: '#E2E8F0' },
  buscaInput: { flex: 1, marginLeft: 8, fontSize: 15, color: '#0F172A' },

  lista: { padding: 12 },

  plantaItem: {
    backgroundColor: '#fff',
    marginBottom: 10,
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#F1F5F9',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  plantaItemSelecionada: { borderColor: '#1B9E5A', borderWidth: 2 },
  plantaItemBaixada: { borderLeftWidth: 4, borderLeftColor: '#16A34A' },

  plantaMainRow: { flexDirection: 'row', padding: 14 },
  plantaInfo: { flex: 1 },
  plantaNameRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  plantaNome: { fontSize: 16, fontWeight: '700', color: '#0F172A' },
  plantaCientifico: { fontSize: 13, fontStyle: 'italic', color: '#94A3B8', marginTop: 2 },
  plantaTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  tag: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#F1F5F9', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  tagComestivel: { backgroundColor: '#F0FDF4', borderWidth: 1, borderColor: '#BBF7D0' },
  tagAR: { backgroundColor: '#EFF6FF', borderWidth: 1, borderColor: '#BFDBFE' },
  tagVariacoes: { backgroundColor: '#FFFBEB', borderWidth: 1, borderColor: '#FDE68A' },
  tagText: { fontSize: 11, color: '#64748B', fontWeight: '600' },

  plantaRight: { alignItems: 'center', justifyContent: 'center', gap: 8, marginLeft: 8 },

  expandedDetails: { paddingHorizontal: 14, paddingBottom: 14 },
  expandedDivider: { height: 1, backgroundColor: '#F1F5F9', marginBottom: 12 },
  expandedSection: { gap: 6, marginBottom: 10 },
  expandedRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  expandedLabel: { fontSize: 14, fontWeight: '700' },
  expandedText: { fontSize: 13, color: '#475569', flex: 1 },
  expandedBold: { fontWeight: '700', color: '#0F172A' },

  expandedEpocaRow: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  expandedEpocaCard: { flex: 1, backgroundColor: '#FFFBEB', borderRadius: 10, padding: 12, alignItems: 'center', borderWidth: 1, borderColor: '#FDE68A' },
  expandedEpocaLabel: { color: '#92400E', fontSize: 11, fontWeight: '600', marginTop: 4 },
  expandedEpocaValue: { color: '#78350F', fontSize: 13, fontWeight: '700', marginTop: 2, textAlign: 'center' },

  expandedFooter: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  expandedMeta: { color: '#94A3B8', fontSize: 12 },

  pacoteItem: { backgroundColor: '#fff', padding: 16, marginBottom: 10, borderRadius: 14, borderWidth: 1, borderColor: '#F1F5F9' },
  pacoteCompleto: { borderLeftWidth: 4, borderLeftColor: '#16A34A' },
  pacoteHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  pacoteNome: { fontSize: 16, fontWeight: '700', color: '#0F172A', flex: 1 },
  pacoteTamanho: { fontSize: 13, color: '#94A3B8', marginLeft: 10, fontWeight: '600' },
  pacoteDescricao: { fontSize: 13, color: '#64748B', marginBottom: 10, lineHeight: 19 },
  pacoteInfo: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  pacoteTag: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#F8FAFC', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8 },
  pacoteTagText: { fontSize: 12, color: '#64748B' },

  progressoContainer: { marginTop: 10, flexDirection: 'row', alignItems: 'center' },
  progressoBarra: { flex: 1, height: 6, backgroundColor: '#F1F5F9', borderRadius: 3, overflow: 'hidden' },
  progressoPreenchido: { height: '100%', backgroundColor: '#1B9E5A', borderRadius: 3 },
  progressoTexto: { fontSize: 12, color: '#64748B', marginLeft: 10, minWidth: 40, fontWeight: '600' },

  emptyContainer: { alignItems: 'center', justifyContent: 'center', paddingVertical: 60 },
  emptyText: { fontSize: 15, color: '#94A3B8', marginTop: 12, textAlign: 'center', paddingHorizontal: 20 },
  emptyHint: { fontSize: 13, color: '#CBD5E1', marginTop: 6, textAlign: 'center', paddingHorizontal: 30 },

  barraAcoes: { flexDirection: 'row', backgroundColor: '#1E293B', paddingVertical: 10, paddingHorizontal: 12, gap: 8, borderTopWidth: 1, borderTopColor: '#334155' },
  botaoAcaoCancel: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10, backgroundColor: '#475569' },
  botaoAcaoAll: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10, backgroundColor: '#0EA5E9' },
  botaoAcaoDownload: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10, backgroundColor: '#1B9E5A', flex: 1, justifyContent: 'center' },
  botaoAcaoTexto: { color: '#fff', fontSize: 13, fontWeight: '700' },

  fab: { position: 'absolute', right: 20, width: 56, height: 56, borderRadius: 16, backgroundColor: '#1B9E5A', justifyContent: 'center', alignItems: 'center', elevation: 6, shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.2, shadowRadius: 6 },
});

export default PlantasOfflineScreen;
