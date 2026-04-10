/**
 * Tela de gerenciamento das plantas já baixadas
 * Mostra plantas offline, permite remover e gerenciar armazenamento
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import plantasOfflineService from '../services/plantasOfflineService';

const MinhasPlantasOfflineScreen = ({ navigation }) => {
  const [plantas, setPlantas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [estatisticas, setEstatisticas] = useState(null);
  const [ordenacao, setOrdenacao] = useState('recente'); // 'recente', 'nome', 'tamanho', 'uso'

  useEffect(() => {
    carregarDados();
  }, []);

  /**
   * Carrega plantas baixadas
   */
  const carregarDados = async () => {
    try {
      setLoading(true);

      const plantasLocal = await plantasOfflineService.listarPlantasBaixadas();

      // Ordena conforme seleção
      const plantasOrdenadas = ordenarPlantas(plantasLocal);
      setPlantas(plantasOrdenadas);

      // Carrega estatísticas
      const stats = await plantasOfflineService.obterEstatisticas();
      setEstatisticas(stats);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      Alert.alert('Erro', 'Erro ao carregar plantas offline');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  /**
   * Ordena plantas conforme critério selecionado
   */
  const ordenarPlantas = (plantasArray) => {
    const copia = [...plantasArray];

    switch (ordenacao) {
      case 'nome':
        return copia.sort((a, b) =>
          (a.dados?.nome_popular || '').localeCompare(b.dados?.nome_popular || '')
        );
      case 'tamanho':
        return copia.sort((a, b) =>
          (b.dados?.tamanho_total_mb || 0) - (a.dados?.tamanho_total_mb || 0)
        );
      case 'uso':
        return copia.sort((a, b) => {
          const vezesA = a.dados?.vezes_identificada || 0;
          const vezesB = b.dados?.vezes_identificada || 0;
          return vezesB - vezesA;
        });
      case 'recente':
      default:
        return copia.sort((a, b) =>
          new Date(b.baixadoEm) - new Date(a.baixadoEm)
        );
    }
  };

  /**
   * Atualiza ordenação
   */
  useEffect(() => {
    if (plantas.length > 0) {
      const plantasOrdenadas = ordenarPlantas(plantas);
      setPlantas(plantasOrdenadas);
    }
  }, [ordenacao]);

  /**
   * Refresh
   */
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    carregarDados();
  }, []);

  /**
   * Remove planta offline
   */
  const removerPlanta = (plantaId, nomePopular) => {
    Alert.alert(
      'Confirmar Remoção',
      `Deseja remover "${nomePopular}" dos dados offline?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Remover',
          style: 'destructive',
          onPress: async () => {
            try {
              setLoading(true);
              await plantasOfflineService.removerPlantaLocal(plantaId);
              Alert.alert('Sucesso', 'Planta removida com sucesso');
              carregarDados();
            } catch (error) {
              Alert.alert('Erro', 'Erro ao remover planta');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  /**
   * Limpa plantas antigas
   */
  const limparPlantasAntigas = () => {
    Alert.alert(
      'Limpar Plantas Antigas',
      'Deseja remover plantas não usadas nos últimos 30 dias?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Limpar',
          onPress: async () => {
            try {
              setLoading(true);
              const resultado = await plantasOfflineService.limparPlantasAntigas(30);

              if (resultado.sucesso) {
                Alert.alert(
                  'Concluído',
                  `${resultado.plantasRemovidas} plantas removidas`
                );
                carregarDados();
              }
            } catch (error) {
              Alert.alert('Erro', 'Erro ao limpar plantas antigas');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  /**
   * Formata data
   */
  const formatarData = (dataISO) => {
    if (!dataISO) return 'Nunca';
    const data = new Date(dataISO);
    return data.toLocaleDateString('pt-BR');
  };

  /**
   * Renderiza item de planta
   */
  const renderPlantaItem = ({ item }) => {
    const dados = item.dados;
    if (!dados) return null;

    return (
      <TouchableOpacity
        style={styles.plantaItem}
        onPress={() => {
          Alert.alert(
            dados.nome_popular || 'Planta Offline',
            `${dados.nome_cientifico || 'Sem nome científico'}\nBaixada em: ${formatarData(item.baixadoEm)}\nTamanho: ${Number(dados.tamanho_total_mb || 0).toFixed(1)} MB`
          );
        }}
      >
        <View style={styles.plantaInfo}>
          <Text style={styles.plantaNome}>{dados.nome_popular}</Text>
          <Text style={styles.plantaCientifico}>{dados.nome_cientifico}</Text>

          <View style={styles.plantaStats}>
            <View style={styles.statItem}>
              <Ionicons name="download" size={14} color="#666" />
              <Text style={styles.statText}>
                {formatarData(item.baixadoEm)}
              </Text>
            </View>

            <View style={styles.statItem}>
              <Ionicons name="search" size={14} color="#666" />
              <Text style={styles.statText}>
                {dados.vezes_identificada || 0}x
              </Text>
            </View>

            <View style={styles.statItem}>
              <Ionicons name="file-tray" size={14} color="#666" />
              <Text style={styles.statText}>
                {(dados.tamanho_total_mb || 0).toFixed(1)} MB
              </Text>
            </View>
          </View>

          {dados.variacoes && dados.variacoes.length > 0 && (
            <View style={styles.variacoesTag}>
              <Ionicons name="layers" size={12} color="#FF9800" />
              <Text style={styles.variacoesText}>
                {dados.variacoes.length} variações
              </Text>
            </View>
          )}
        </View>

        <TouchableOpacity
          style={styles.botaoRemover}
          onPress={() => removerPlanta(item.id, dados.nome_popular)}
        >
          <Ionicons name="trash-outline" size={24} color="#f44336" />
        </TouchableOpacity>
      </TouchableOpacity>
    );
  };

  /**
   * Renderiza header com estatísticas
   */
  const renderHeader = () => (
    <View style={styles.header}>
      {estatisticas && (
        <>
          <View style={styles.estatisticasCard}>
            <View style={styles.estatRow}>
              <View style={styles.estatItem}>
                <Text style={styles.estatValor}>
                  {estatisticas.totalPlantas}
                </Text>
                <Text style={styles.estatLabel}>Plantas Baixadas</Text>
              </View>

              <View style={styles.estatItem}>
                <Text style={styles.estatValor}>
                  {estatisticas.tamanhoTotalMb.toFixed(1)} MB
                </Text>
                <Text style={styles.estatLabel}>Espaço Usado</Text>
              </View>
            </View>

            {/* Barra de progresso */}
            <View style={styles.progressoContainer}>
              <View style={styles.progressoBarra}>
                <View
                  style={[
                    styles.progressoPreenchido,
                    {
                      width: `${estatisticas.percentualUsado}%`,
                      backgroundColor:
                        estatisticas.percentualUsado > 80 ? '#f44336' : '#4CAF50',
                    },
                  ]}
                />
              </View>
              <Text style={styles.progressoTexto}>
                {estatisticas.percentualUsado}% de {estatisticas.limiteMb} MB
              </Text>
            </View>
          </View>

          {/* Botão de limpeza */}
          {estatisticas.totalPlantas > 0 && (
            <TouchableOpacity
              style={styles.botaoLimpar}
              onPress={limparPlantasAntigas}
            >
              <Ionicons name="trash" size={20} color="#f44336" />
              <Text style={styles.botaoLimparTexto}>
                Limpar Plantas Antigas
              </Text>
            </TouchableOpacity>
          )}
        </>
      )}

      {/* Ordenação */}
      <View style={styles.ordenacaoContainer}>
        <Text style={styles.ordenacaoLabel}>Ordenar por:</Text>
        <View style={styles.ordenacaoBotoes}>
          {[
            { key: 'recente', label: 'Recentes', icon: 'time' },
            { key: 'nome', label: 'Nome', icon: 'text' },
            { key: 'tamanho', label: 'Tamanho', icon: 'file-tray' },
            { key: 'uso', label: 'Uso', icon: 'search' },
          ].map((op) => (
            <TouchableOpacity
              key={op.key}
              style={[
                styles.ordenacaoBotao,
                ordenacao === op.key && styles.ordenacaoBotaoAtivo,
              ]}
              onPress={() => setOrdenacao(op.key)}
            >
              <Ionicons
                name={op.icon}
                size={16}
                color={ordenacao === op.key ? '#fff' : '#666'}
              />
              <Text
                style={[
                  styles.ordenacaoBotaoTexto,
                  ordenacao === op.key && styles.ordenacaoBotaoTextoAtivo,
                ]}
              >
                {op.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </View>
  );

  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Carregando...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {renderHeader()}

      <FlatList
        data={plantas}
        renderItem={renderPlantaItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.lista}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="folder-open-outline" size={64} color="#ccc" />
            <Text style={styles.emptyText}>
              Nenhuma planta baixada ainda
            </Text>
            <TouchableOpacity
              style={styles.botaoBaixar}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.botaoBaixarTexto}>
                Baixar Plantas
              </Text>
            </TouchableOpacity>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  header: {
    backgroundColor: '#fff',
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  estatisticasCard: {
    padding: 15,
    backgroundColor: '#fff',
  },
  estatRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
  },
  estatItem: {
    alignItems: 'center',
  },
  estatValor: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  estatLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  progressoContainer: {
    marginTop: 10,
  },
  progressoBarra: {
    height: 8,
    backgroundColor: '#e0e0e0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressoPreenchido: {
    height: '100%',
  },
  progressoTexto: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
    textAlign: 'center',
  },
  botaoLimpar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    marginHorizontal: 15,
    marginVertical: 10,
    backgroundColor: '#ffebee',
    borderRadius: 8,
  },
  botaoLimparTexto: {
    fontSize: 14,
    color: '#f44336',
    fontWeight: 'bold',
    marginLeft: 8,
  },
  ordenacaoContainer: {
    padding: 15,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  ordenacaoLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  ordenacaoBotoes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  ordenacaoBotao: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: '#f5f5f5',
    borderRadius: 16,
  },
  ordenacaoBotaoAtivo: {
    backgroundColor: '#4CAF50',
  },
  ordenacaoBotaoTexto: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  ordenacaoBotaoTextoAtivo: {
    color: '#fff',
  },
  lista: {
    padding: 10,
  },
  plantaItem: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 15,
    marginBottom: 10,
    borderRadius: 10,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  plantaInfo: {
    flex: 1,
  },
  plantaNome: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  plantaCientifico: {
    fontSize: 14,
    fontStyle: 'italic',
    color: '#666',
    marginTop: 2,
  },
  plantaStats: {
    flexDirection: 'row',
    marginTop: 8,
    flexWrap: 'wrap',
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 15,
    marginBottom: 4,
  },
  statText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 4,
  },
  variacoesTag: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: '#FFF3E0',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 8,
  },
  variacoesText: {
    fontSize: 11,
    color: '#FF9800',
    marginLeft: 4,
  },
  botaoRemover: {
    justifyContent: 'center',
    paddingLeft: 15,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 50,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
    marginTop: 10,
    marginBottom: 20,
  },
  botaoBaixar: {
    backgroundColor: '#4CAF50',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  botaoBaixarTexto: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default MinhasPlantasOfflineScreen;
