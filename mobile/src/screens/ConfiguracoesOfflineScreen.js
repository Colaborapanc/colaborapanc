/**
 * Tela de configurações offline
 * Permite gerenciar preferências de download e armazenamento
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import plantasOfflineService from '../services/plantasOfflineService';
import Slider from '@react-native-community/slider';

const ConfiguracoesOfflineScreen = ({ navigation }) => {
  const [loading, setLoading] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [config, setConfig] = useState(null);
  const [estatisticas, setEstatisticas] = useState(null);

  useEffect(() => {
    carregarDados();
  }, []);

  /**
   * Carrega configurações e estatísticas
   */
  const carregarDados = async () => {
    try {
      setLoading(true);

      // Carrega configurações
      const resultadoConfig = await plantasOfflineService.obterConfiguracoes();
      if (resultadoConfig.sucesso) {
        setConfig(resultadoConfig.configuracoes);
      }

      // Carrega estatísticas
      const stats = await plantasOfflineService.obterEstatisticas();
      setEstatisticas(stats);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      Alert.alert('Erro', 'Erro ao carregar configurações');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Salva configurações
   */
  const salvarConfiguracoes = async () => {
    try {
      setSalvando(true);

      const resultado = await plantasOfflineService.atualizarConfiguracoes(config);

      if (resultado.sucesso) {
        Alert.alert('Sucesso', 'Configurações salvas com sucesso');
      } else {
        Alert.alert('Erro', resultado.erro);
      }
    } catch (error) {
      Alert.alert('Erro', 'Erro ao salvar configurações');
    } finally {
      setSalvando(false);
    }
  };

  /**
   * Atualiza uma configuração
   */
  const atualizarConfig = (chave, valor) => {
    setConfig(prev => ({
      ...prev,
      [chave]: valor,
    }));
  };

  /**
   * Limpa todo o cache offline
   */
  const limparCacheCompleto = () => {
    Alert.alert(
      'Confirmar Limpeza',
      'Deseja remover TODAS as plantas baixadas? Esta ação não pode ser desfeita.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Limpar Tudo',
          style: 'destructive',
          onPress: async () => {
            try {
              setLoading(true);

              const plantasBaixadas = await plantasOfflineService.listarPlantasBaixadas();

              for (const planta of plantasBaixadas) {
                await plantasOfflineService.removerPlantaLocal(planta.id);
              }

              Alert.alert('Concluído', 'Cache limpo com sucesso');
              carregarDados();
            } catch (error) {
              Alert.alert('Erro', 'Erro ao limpar cache');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  /**
   * Renderiza item de configuração com switch
   */
  const renderSwitchConfig = (titulo, descricao, chave, icone) => (
    <View style={styles.configItem}>
      <View style={styles.configIconContainer}>
        <Ionicons name={icone} size={24} color="#4CAF50" />
      </View>
      <View style={styles.configInfo}>
        <Text style={styles.configTitulo}>{titulo}</Text>
        <Text style={styles.configDescricao}>{descricao}</Text>
      </View>
      <Switch
        value={config[chave]}
        onValueChange={(valor) => atualizarConfig(chave, valor)}
        trackColor={{ false: '#ccc', true: '#81C784' }}
        thumbColor={config[chave] ? '#4CAF50' : '#f4f3f4'}
      />
    </View>
  );

  /**
   * Renderiza seletor de qualidade
   */
  const renderQualidadeSelector = () => (
    <View style={styles.configItem}>
      <View style={styles.configIconContainer}>
        <Ionicons name="image" size={24} color="#4CAF50" />
      </View>
      <View style={styles.configInfo}>
        <Text style={styles.configTitulo}>Qualidade das Fotos</Text>
        <View style={styles.qualidadeOpcoes}>
          {['baixa', 'media', 'alta'].map((qualidade) => (
            <TouchableOpacity
              key={qualidade}
              style={[
                styles.qualidadeOpcao,
                config.qualidade_fotos === qualidade && styles.qualidadeOpcaoAtiva,
              ]}
              onPress={() => atualizarConfig('qualidade_fotos', qualidade)}
            >
              <Text
                style={[
                  styles.qualidadeOpcaoTexto,
                  config.qualidade_fotos === qualidade && styles.qualidadeOpcaoTextoAtiva,
                ]}
              >
                {qualidade.charAt(0).toUpperCase() + qualidade.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.configDescricao}>
          {config.qualidade_fotos === 'baixa' && 'Menor tamanho, menor qualidade'}
          {config.qualidade_fotos === 'media' && 'Balanceado entre qualidade e tamanho'}
          {config.qualidade_fotos === 'alta' && 'Melhor qualidade, maior tamanho'}
        </Text>
      </View>
    </View>
  );

  /**
   * Renderiza slider de limite de armazenamento
   */
  const renderLimiteArmazenamento = () => (
    <View style={styles.configItem}>
      <View style={styles.configIconContainer}>
        <Ionicons name="server" size={24} color="#4CAF50" />
      </View>
      <View style={styles.configInfo}>
        <Text style={styles.configTitulo}>Limite de Armazenamento</Text>
        <View style={styles.sliderContainer}>
          <Text style={styles.sliderValor}>
            {config.limite_armazenamento_mb} MB
          </Text>
          <Slider
            style={styles.slider}
            minimumValue={100}
            maximumValue={2000}
            step={50}
            value={config.limite_armazenamento_mb}
            onValueChange={(valor) => atualizarConfig('limite_armazenamento_mb', valor)}
            minimumTrackTintColor="#4CAF50"
            maximumTrackTintColor="#ccc"
            thumbTintColor="#4CAF50"
          />
        </View>
        <Text style={styles.configDescricao}>
          Espaço máximo para dados offline
        </Text>
      </View>
    </View>
  );

  /**
   * Renderiza seletor de frequência de atualização
   */
  const renderFrequenciaSelector = () => (
    <View style={styles.configItem}>
      <View style={styles.configIconContainer}>
        <Ionicons name="sync" size={24} color="#4CAF50" />
      </View>
      <View style={styles.configInfo}>
        <Text style={styles.configTitulo}>Frequência de Atualização</Text>
        <View style={styles.frequenciaOpcoes}>
          {[
            { key: 'diaria', label: 'Diária' },
            { key: 'semanal', label: 'Semanal' },
            { key: 'mensal', label: 'Mensal' },
            { key: 'manual', label: 'Manual' },
          ].map((freq) => (
            <TouchableOpacity
              key={freq.key}
              style={[
                styles.frequenciaOpcao,
                config.frequencia_atualizacao === freq.key && styles.frequenciaOpcaoAtiva,
              ]}
              onPress={() => atualizarConfig('frequencia_atualizacao', freq.key)}
            >
              <Text
                style={[
                  styles.frequenciaOpcaoTexto,
                  config.frequencia_atualizacao === freq.key && styles.frequenciaOpcaoTextoAtiva,
                ]}
              >
                {freq.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Carregando configurações...</Text>
      </View>
    );
  }

  if (!config) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle" size={64} color="#f44336" />
        <Text style={styles.errorText}>Erro ao carregar configurações</Text>
        <TouchableOpacity style={styles.botaoRetentar} onPress={carregarDados}>
          <Text style={styles.botaoRetentarTexto}>Tentar Novamente</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Estatísticas */}
        {estatisticas && (
          <View style={styles.secao}>
            <Text style={styles.secaoTitulo}>Armazenamento</Text>

            <View style={styles.estatisticasCard}>
              <View style={styles.progressoCircular}>
                <Text style={styles.progressoValor}>
                  {estatisticas.percentualUsado}%
                </Text>
                <Text style={styles.progressoLabel}>Usado</Text>
              </View>

              <View style={styles.estatisticasDetalhes}>
                <View style={styles.estatItem}>
                  <Text style={styles.estatLabel}>Plantas Baixadas</Text>
                  <Text style={styles.estatValor}>{estatisticas.totalPlantas}</Text>
                </View>

                <View style={styles.estatItem}>
                  <Text style={styles.estatLabel}>Espaço Usado</Text>
                  <Text style={styles.estatValor}>
                    {estatisticas.tamanhoTotalMb.toFixed(1)} MB
                  </Text>
                </View>

                <View style={styles.estatItem}>
                  <Text style={styles.estatLabel}>Disponível</Text>
                  <Text style={styles.estatValor}>
                    {(estatisticas.limiteMb - estatisticas.tamanhoTotalMb).toFixed(1)} MB
                  </Text>
                </View>
              </View>
            </View>

            {/* Barra de progresso */}
            <View style={styles.progressoBarraContainer}>
              <View style={styles.progressoBarra}>
                <View
                  style={[
                    styles.progressoPreenchido,
                    {
                      width: `${estatisticas.percentualUsado}%`,
                      backgroundColor:
                        estatisticas.percentualUsado > 90
                          ? '#f44336'
                          : estatisticas.percentualUsado > 70
                          ? '#FF9800'
                          : '#4CAF50',
                    },
                  ]}
                />
              </View>
            </View>
          </View>
        )}

        {/* Download */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>Download</Text>

          {renderSwitchConfig(
            'Baixar Apenas com WiFi',
            'Downloads automáticos apenas quando conectado ao WiFi',
            'baixar_apenas_wifi',
            'wifi'
          )}

          {renderQualidadeSelector()}

          {renderSwitchConfig(
            'Incluir Modelos AR',
            'Baixar modelos 3D para realidade aumentada (ocupa mais espaço)',
            'incluir_modelos_ar',
            'cube'
          )}
        </View>

        {/* Armazenamento */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>Gerenciamento</Text>

          {renderLimiteArmazenamento()}

          {renderSwitchConfig(
            'Limpar Plantas Antigas',
            'Remover automaticamente plantas não usadas há mais de 30 dias',
            'auto_limpar_antigas',
            'trash'
          )}
        </View>

        {/* Atualização */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>Atualização</Text>

          {renderSwitchConfig(
            'Atualizar Automaticamente',
            'Manter plantas offline atualizadas',
            'auto_atualizar',
            'sync'
          )}

          {config.auto_atualizar && renderFrequenciaSelector()}
        </View>

        {/* Ações */}
        <View style={styles.secao}>
          <Text style={styles.secaoTitulo}>Ações</Text>

          <TouchableOpacity
            style={styles.botaoAcao}
            onPress={limparCacheCompleto}
          >
            <Ionicons name="trash" size={20} color="#f44336" />
            <Text style={[styles.botaoAcaoTexto, { color: '#f44336' }]}>
              Limpar Todo o Cache
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.botaoAcao}
            onPress={() => navigation.navigate('MinhasPlantas')}
          >
            <Ionicons name="folder-open" size={20} color="#2196F3" />
            <Text style={[styles.botaoAcaoTexto, { color: '#2196F3' }]}>
              Gerenciar Plantas Baixadas
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Botão de salvar */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.botaoSalvar, salvando && styles.botaoSalvarDisabled]}
          onPress={salvarConfiguracoes}
          disabled={salvando}
        >
          {salvando ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Ionicons name="checkmark-circle" size={24} color="#fff" />
              <Text style={styles.botaoSalvarTexto}>Salvar Configurações</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#666',
    marginTop: 15,
    textAlign: 'center',
  },
  botaoRetentar: {
    marginTop: 20,
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: '#4CAF50',
    borderRadius: 8,
  },
  botaoRetentarTexto: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
  },
  secao: {
    marginTop: 10,
    backgroundColor: '#fff',
    paddingVertical: 15,
  },
  secaoTitulo: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    paddingHorizontal: 15,
    marginBottom: 15,
  },
  estatisticasCard: {
    flexDirection: 'row',
    paddingHorizontal: 15,
    marginBottom: 15,
  },
  progressoCircular: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#E8F5E9',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 20,
  },
  progressoValor: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  progressoLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  estatisticasDetalhes: {
    flex: 1,
    justifyContent: 'space-around',
  },
  estatItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  estatLabel: {
    fontSize: 14,
    color: '#666',
  },
  estatValor: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  progressoBarraContainer: {
    paddingHorizontal: 15,
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
  configItem: {
    flexDirection: 'row',
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  configIconContainer: {
    width: 40,
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 2,
  },
  configInfo: {
    flex: 1,
    paddingRight: 10,
  },
  configTitulo: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 4,
  },
  configDescricao: {
    fontSize: 13,
    color: '#666',
  },
  qualidadeOpcoes: {
    flexDirection: 'row',
    marginVertical: 8,
  },
  qualidadeOpcao: {
    flex: 1,
    paddingVertical: 8,
    marginRight: 8,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    alignItems: 'center',
  },
  qualidadeOpcaoAtiva: {
    backgroundColor: '#4CAF50',
  },
  qualidadeOpcaoTexto: {
    fontSize: 14,
    color: '#666',
  },
  qualidadeOpcaoTextoAtiva: {
    color: '#fff',
    fontWeight: 'bold',
  },
  sliderContainer: {
    marginVertical: 10,
  },
  sliderValor: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#4CAF50',
    marginBottom: 5,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  frequenciaOpcoes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginVertical: 8,
  },
  frequenciaOpcao: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: '#f5f5f5',
    borderRadius: 16,
  },
  frequenciaOpcaoAtiva: {
    backgroundColor: '#4CAF50',
  },
  frequenciaOpcaoTexto: {
    fontSize: 13,
    color: '#666',
  },
  frequenciaOpcaoTextoAtiva: {
    color: '#fff',
    fontWeight: 'bold',
  },
  botaoAcao: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    paddingHorizontal: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  botaoAcaoTexto: {
    fontSize: 16,
    marginLeft: 15,
  },
  footer: {
    backgroundColor: '#fff',
    padding: 15,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  botaoSalvar: {
    flexDirection: 'row',
    backgroundColor: '#4CAF50',
    paddingVertical: 15,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  botaoSalvarDisabled: {
    backgroundColor: '#ccc',
  },
  botaoSalvarTexto: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});

export default ConfiguracoesOfflineScreen;
