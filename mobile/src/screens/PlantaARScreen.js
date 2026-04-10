/**
 * Tela de Realidade Aumentada para Visualização de Plantas
 *
 * Permite visualizar modelos 3D de plantas em AR usando expo-gl
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  Dimensions,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { GLView } from 'expo-gl';
import * as FileSystem from 'expo-file-system';
import identificacaoService from '../services/identificacaoService';

const { width, height } = Dimensions.get('window');

export default function PlantaARScreen({ route, navigation }) {
  const { plantaId, plantaNome } = route.params || {};

  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [loading, setLoading] = useState(true);
  const [modelosAR, setModelosAR] = useState([]);
  const [modeloSelecionado, setModeloSelecionado] = useState(null);
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [arAtivo, setArAtivo] = useState(false);
  const [cameraError, setCameraError] = useState(null);

  const glRef = useRef(null);

  useEffect(() => {
    if (!cameraPermission) return;
    if (!cameraPermission.granted && cameraPermission.canAskAgain) {
      requestCameraPermission();
    }
  }, [cameraPermission, requestCameraPermission]);

  useEffect(() => {
    carregarModelosAR();
  }, []);

  const carregarModelosAR = async () => {
    setLoading(true);

    try {
      const resultado = await identificacaoService.obterModelosAR(plantaId);

      if (resultado.sucesso && resultado.modelos.length > 0) {
        setModelosAR(resultado.modelos);

        // Selecionar primeiro modelo por padrão
        setModeloSelecionado(resultado.modelos[0]);
      } else {
        Alert.alert(
          'Sem Modelos AR',
          'Não há modelos 3D disponíveis para esta planta ainda.',
          [
            { text: 'OK', onPress: () => navigation.goBack() }
          ]
        );
      }
    } catch (error) {
      console.error('Erro ao carregar modelos AR:', error);
      Alert.alert('Erro', 'Não foi possível carregar os modelos 3D.');
    } finally {
      setLoading(false);
    }
  };

  const iniciarAR = async () => {
    if (!modeloSelecionado) {
      Alert.alert('Erro', 'Selecione um modelo 3D primeiro.');
      return;
    }

    setArAtivo(true);
  };

  const pararAR = () => {
    setArAtivo(false);
  };

  const renderModeloItem = ({ item }) => (
    <TouchableOpacity
      style={[
        styles.modeloItem,
        modeloSelecionado?.id === item.id && styles.modeloItemSelecionado,
      ]}
      onPress={() => {
        setModeloSelecionado(item);
        setShowModelSelector(false);
      }}
    >
      <Text style={styles.modeloNome}>{item.nome}</Text>
      <Text style={styles.modeloDescricao}>{item.descricao}</Text>
      <Text style={styles.modeloFormato}>
        Formato: {item.formato.toUpperCase()}
      </Text>
    </TouchableOpacity>
  );

  if (!cameraPermission) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Solicitando permissão da câmera...</Text>
      </View>
    );
  }

  if (!cameraPermission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>
          Sem acesso à câmera. Por favor, permita o acesso nas configurações.
        </Text>
        {cameraPermission.canAskAgain && (
          <TouchableOpacity
            style={styles.button}
            onPress={requestCameraPermission}
          >
            <Text style={styles.buttonText}>Permitir câmera</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.buttonText}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Carregando modelos 3D...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>← Voltar</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {plantaNome || 'Visualização AR'}
        </Text>
      </View>

      {/* Câmera / Visualização AR */}
      <View style={styles.cameraContainer}>
        {!arAtivo ? (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>
              Aponte a câmera para uma superfície plana
            </Text>
            <Text style={styles.placeholderSubtext}>
              Pressione "Iniciar AR" para visualizar a planta em 3D
            </Text>
          </View>
        ) : cameraError ? (
          <View style={styles.placeholder}>
            <Text style={styles.errorText}>Não foi possível abrir a câmera.</Text>
            <Text style={styles.placeholderSubtext}>Detalhe: {cameraError}</Text>
          </View>
        ) : (
          <CameraView
            style={styles.camera}
            facing="back"
            onMountError={(event) => {
              const reason = event?.nativeEvent?.message || 'erro_desconhecido';
              setCameraError(reason);
            }}
          >
            {/* Aqui seria integrado o motor AR (ARKit/ARCore) */}
            {/* Por enquanto, mostramos um placeholder */}
            <View style={styles.arOverlay}>
              <Text style={styles.arText}>
                Modo AR Ativo
              </Text>
              <Text style={styles.arSubtext}>
                {modeloSelecionado?.nome}
              </Text>
            </View>
          </CameraView>
        )}
      </View>

      {/* Controles */}
      <View style={styles.controls}>
        {/* Botão Selecionar Modelo */}
        <TouchableOpacity
          style={[styles.controlButton, styles.selectButton]}
          onPress={() => setShowModelSelector(true)}
        >
          <Text style={styles.controlButtonText}>
            📦 {modeloSelecionado ? modeloSelecionado.nome : 'Selecionar Modelo'}
          </Text>
        </TouchableOpacity>

        {/* Botão Iniciar/Parar AR */}
        <TouchableOpacity
          style={[
            styles.controlButton,
            arAtivo ? styles.stopButton : styles.startButton,
          ]}
          onPress={arAtivo ? pararAR : iniciarAR}
        >
          <Text style={styles.controlButtonText}>
            {arAtivo ? '⏸️ Parar AR' : '▶️ Iniciar AR'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Informações do Modelo */}
      {modeloSelecionado && (
        <View style={styles.infoPanel}>
          <Text style={styles.infoTitle}>Informações do Modelo</Text>
          <Text style={styles.infoText}>
            Planta: {modeloSelecionado.planta?.nome_popular || 'N/A'}
          </Text>
          <Text style={styles.infoText}>
            Tamanho: {(modeloSelecionado.tamanho_arquivo / 1024 / 1024).toFixed(2)} MB
          </Text>
          <Text style={styles.infoText}>
            Interativo: {modeloSelecionado.permite_interacao ? 'Sim' : 'Não'}
          </Text>
        </View>
      )}

      {/* Modal de Seleção de Modelo */}
      <Modal
        visible={showModelSelector}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowModelSelector(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Selecionar Modelo 3D</Text>
              <TouchableOpacity
                onPress={() => setShowModelSelector(false)}
              >
                <Text style={styles.modalCloseButton}>✕</Text>
              </TouchableOpacity>
            </View>

            <FlatList
              data={modelosAR}
              renderItem={renderModeloItem}
              keyExtractor={(item) => item.id.toString()}
              style={styles.modelosList}
            />
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#1a1a1a',
  },
  backButton: {
    padding: 8,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
  },
  headerTitle: {
    flex: 1,
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 16,
  },
  cameraContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
  },
  placeholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  placeholderText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  placeholderSubtext: {
    color: '#ccc',
    fontSize: 14,
    textAlign: 'center',
  },
  arOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  arText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  arSubtext: {
    color: '#fff',
    fontSize: 16,
    marginTop: 10,
  },
  controls: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#1a1a1a',
    gap: 10,
  },
  controlButton: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectButton: {
    backgroundColor: '#2196F3',
  },
  startButton: {
    backgroundColor: '#4CAF50',
  },
  stopButton: {
    backgroundColor: '#f44336',
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  infoPanel: {
    padding: 16,
    backgroundColor: '#1a1a1a',
  },
  infoTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  infoText: {
    color: '#ccc',
    fontSize: 14,
    marginVertical: 2,
  },
  loadingText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 20,
  },
  errorText: {
    color: '#f44336',
    fontSize: 16,
    textAlign: 'center',
    padding: 20,
  },
  button: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 8,
    marginTop: 20,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: height * 0.7,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalCloseButton: {
    fontSize: 24,
    color: '#666',
  },
  modelosList: {
    padding: 16,
  },
  modeloItem: {
    padding: 16,
    marginBottom: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  modeloItemSelecionado: {
    borderColor: '#4CAF50',
    backgroundColor: '#e8f5e9',
  },
  modeloNome: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  modeloDescricao: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  modeloFormato: {
    fontSize: 12,
    color: '#999',
  },
});
