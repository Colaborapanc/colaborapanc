/**
 * Tela de Identificação de Plantas
 *
 * Similar ao Google Lens - captura foto e identifica a planta
 * usando múltiplas fontes (Custom DB, Google Vision, PlantNet, Plant.id)
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Image,
  ScrollView,
  Dimensions,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import identificacaoService from '../services/identificacaoService';
import autoDetectionService from '../services/autoDetectionService';

const { width, height } = Dimensions.get('window');

export default function IdentificarPlantaScreen({ navigation, route }) {
  const { pontoId } = route.params || {};
  const insets = useSafeAreaInsets();

  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [facing] = useState('back');
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [identifying, setIdentifying] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [showCamera, setShowCamera] = useState(true);
  const [modoDeteccao, setModoDeteccao] = useState('assistido');
  const [deteccaoAoVivo, setDeteccaoAoVivo] = useState(false);

  const cameraRef = useRef(null);

  useEffect(() => {
    if (!cameraPermission) return;
    if (!cameraPermission.granted && cameraPermission.canAskAgain) {
      requestCameraPermission();
    }
  }, [cameraPermission, requestCameraPermission]);

  const tirarFoto = async () => {
    if (!cameraReady || !cameraRef.current) {
      Alert.alert('Erro', 'Câmera não está pronta');
      return;
    }

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.7,
        base64: false,
      });

      setCapturedPhoto(photo.uri);
      setShowCamera(false);
    } catch (error) {
      console.error('Erro ao tirar foto:', error);
      Alert.alert('Erro', 'Não foi possível tirar a foto');
    }
  };

  const escolherDaGaleria = async () => {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();

      if (status !== 'granted') {
        Alert.alert('Erro', 'Permissão negada para acessar galeria');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaType?.images
          ? [ImagePicker.MediaType.images]
          : ['images'],
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.7,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        setCapturedPhoto(result.assets[0].uri);
        setShowCamera(false);
      }
    } catch (error) {
      console.error('Erro ao escolher da galeria:', error);
      Alert.alert('Erro', 'Não foi possível selecionar imagem');
    }
  };

  const identificarPlanta = async () => {
    if (!capturedPhoto) {
      Alert.alert('Erro', 'Nenhuma foto capturada');
      return;
    }

    setIdentifying(true);
    setResultado(null);

    try {
      const resultado = await identificacaoService.identificarPlanta(
        capturedPhoto,
        {
          usarCustomDB: true,
          usarGoogle: true,
          salvarHistorico: true,
          pontoId: pontoId,
        }
      );

      if (resultado.sucesso) {
        const resultadoFormatado = identificacaoService.formatarResultadoIdentificacao(resultado);
        setResultado({ ...resultadoFormatado, dadosCompletos: resultado.dados });
      } else {
        Alert.alert(
          'Não Identificada',
          resultado.erro || 'Não foi possível identificar a planta. Tente outra foto.',
          [{ text: 'Tentar Novamente', onPress: resetar }]
        );
      }
    } catch (error) {
      console.error('Erro ao identificar:', error);
      Alert.alert('Erro', 'Erro ao processar identificação');
    } finally {
      setIdentifying(false);
    }
  };

  const identificarComIA = async () => {
    if (!capturedPhoto) {
      Alert.alert('Erro', 'Nenhuma foto capturada');
      return;
    }

    setIdentifying(true);
    setResultado(null);

    try {
      const respostaIA = await identificacaoService.identificarPlanta(capturedPhoto, {
        usarCustomDB: true,
        usarGoogle: true,
        salvarHistorico: true,
        pontoId,
        forcarOnline: true,
        tentarOfflinePrimeiro: false,
      });

      if (!respostaIA?.sucesso) {
        Alert.alert('IA indisponível', respostaIA?.erro || 'Não foi possível identificar usando IA online.');
        return;
      }

      const resultadoFormatado = identificacaoService.formatarResultadoIdentificacao(respostaIA);
      setResultado({ ...resultadoFormatado, dadosCompletos: respostaIA.dados });
    } catch (error) {
      Alert.alert('Erro', 'Falha ao identificar com IA online.');
    } finally {
      setIdentifying(false);
    }
  };

  const detectarAutomaticamente = async () => {
    if (!capturedPhoto) {
      Alert.alert('Erro', 'Nenhuma foto capturada');
      return;
    }

    setIdentifying(true);
    try {
      const resultadoAuto = await autoDetectionService.processarDeteccaoAutomatica({
        imageUri: capturedPhoto,
        observacao: resultado?.descricao || '',
        modo: modoDeteccao,
      });

      if (resultadoAuto.ignorado) {
        Alert.alert('Detecção ignorada', 'Cooldown ativo para evitar duplicidade de registros.');
        return;
      }

      if (!resultadoAuto.sucesso) {
        Alert.alert('Detecção automática', resultadoAuto.erro || 'Não foi possível detectar a espécie selecionada offline.');
        return;
      }

      Alert.alert(
        'Detecção registrada',
        `Status: ${resultadoAuto.statusDeteccao}\nConfiança: ${(resultadoAuto.confianca * 100).toFixed(0)}%\nSincronização: ${resultadoAuto.pontoLocal.status_sync}`
      );
    } catch (error) {
      Alert.alert('Erro', 'Falha ao processar detecção automática.');
    } finally {
      setIdentifying(false);
    }
  };

  const usarEmCadastro = (res) => {
    navigation.navigate('CadastroPonto', {
      plantaIdentificada: {
        nomePopular: res.nomePopular,
        nomeCientifico: res.nomeCientifico,
        plantaId: res.plantaId,
        fotoUri: capturedPhoto || null,
      },
    });
  };

  const resetar = () => {
    setCapturedPhoto(null);
    setResultado(null);
    setCameraError(null);
    setShowCamera(true);
  };

  useEffect(() => {
    if (!deteccaoAoVivo || !showCamera || !cameraReady || !cameraRef.current) return undefined;

    const intervalId = setInterval(async () => {
      if (identifying) return;

      try {
        setIdentifying(true);
        const frame = await cameraRef.current.takePictureAsync({
          quality: 0.4,
          skipProcessing: true,
          base64: false,
        });

        const identificacao = await identificacaoService.identificarPlanta(frame.uri, {
          usarCustomDB: true,
          usarGoogle: true,
          salvarHistorico: false,
          pontoId,
          tentarOfflinePrimeiro: false,
        });

        if (identificacao?.sucesso) {
          const formatted = identificacaoService.formatarResultadoIdentificacao(identificacao);
          setResultado({ ...formatted, dadosCompletos: identificacao.dados });
        }
      } catch (error) {
        // Modo contínuo: falhas pontuais não devem interromper câmera
      } finally {
        setIdentifying(false);
      }
    }, 3500);

    return () => clearInterval(intervalId);
  }, [deteccaoAoVivo, showCamera, cameraReady, identifying, pontoId]);

  if (!cameraPermission) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#1B9E5A" />
      </View>
    );
  }

  if (!cameraPermission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Ionicons name="camera-outline" size={64} color="#94A3B8" />
        <Text style={styles.permissionText}>
          Sem acesso à câmera. Por favor, permita o acesso nas configurações.
        </Text>
        {cameraPermission.canAskAgain && (
          <TouchableOpacity style={styles.permissionBtn} onPress={requestCameraPermission}>
            <Ionicons name="camera" size={20} color="#fff" />
            <Text style={styles.permissionBtnText}>Permitir câmera</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={styles.permissionBtnSecondary} onPress={() => navigation.goBack()}>
          <Text style={styles.permissionBtnSecondaryText}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const dadosPlanta = resultado?.dadosCompletos || {};

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerBtn} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={22} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Identificar Planta</Text>
        <TouchableOpacity style={styles.headerBtn} onPress={escolherDaGaleria}>
          <Ionicons name="images-outline" size={22} color="#fff" />
        </TouchableOpacity>
      </View>

      {/* Câmera ou Preview da Foto */}
      <View style={styles.cameraContainer}>
        {showCamera && !capturedPhoto ? (
          cameraError ? (
            <View style={styles.cameraFallback}>
              <Ionicons name="camera-outline" size={48} color="#64748B" />
              <Text style={styles.errorText}>Não foi possível abrir a câmera.</Text>
              <Text style={styles.hint}>Detalhe: {cameraError}</Text>
            </View>
          ) : (
            <CameraView
              ref={cameraRef}
              style={styles.camera}
              facing={facing}
              onCameraReady={() => setCameraReady(true)}
              onMountError={(event) => {
                const reason = event?.nativeEvent?.message || 'erro_desconhecido';
                setCameraError(reason);
              }}
            />
          )
        ) : (
          <View style={styles.previewContainer}>
            <Image
              source={{ uri: capturedPhoto }}
              style={styles.preview}
              resizeMode="contain"
            />
          </View>
        )}
        {showCamera && !capturedPhoto && (
          <View pointerEvents="none" style={styles.cameraOverlay}>
            <View style={styles.targetFrame}>
              <View style={styles.targetCorner1} />
              <View style={styles.targetCorner2} />
              <View style={styles.targetCorner3} />
              <View style={styles.targetCorner4} />
              <Text style={styles.targetText}>Enquadre a planta</Text>
            </View>
          </View>
        )}
      </View>

      {/* Resultado da Identificação */}
      {resultado && (
        <ScrollView style={styles.resultContainer} contentContainerStyle={styles.resultContent}>
          <View style={styles.resultCard}>
            {/* Header do resultado */}
            <View style={styles.resultHeader}>
              <View style={styles.resultStatusRow}>
                <Ionicons
                  name={resultado.identificado ? 'checkmark-circle' : 'close-circle'}
                  size={22}
                  color={resultado.identificado ? '#16A34A' : '#DC2626'}
                />
                <Text style={[styles.resultStatus, { color: resultado.identificado ? '#16A34A' : '#DC2626' }]}>
                  {resultado.identificado ? 'Identificada' : 'Não Identificada'}
                </Text>
              </View>
              <View style={[
                styles.confidenceBadge,
                resultado.confianca >= 70 ? styles.highConfidence :
                resultado.confianca >= 50 ? styles.mediumConfidence :
                styles.lowConfidence
              ]}>
                <Text style={styles.confidenceText}>{resultado.confianca}%</Text>
              </View>
            </View>

            {/* Nome */}
            <Text style={styles.plantName}>{resultado.nomePopular}</Text>
            {!!resultado.nomeCientifico && (
              <Text style={styles.scientificName}>{resultado.nomeCientifico}</Text>
            )}

            {/* Info da planta das integrações */}
            {(!!dadosPlanta.parte_comestivel || !!dadosPlanta.forma_uso || !!dadosPlanta.epoca_frutificacao || !!dadosPlanta.epoca_colheita) && (
              <View style={styles.plantInfoSection}>
                {dadosPlanta.parte_comestivel ? (
                  <View style={styles.plantInfoRow}>
                    <Ionicons name="checkmark-circle" size={16} color="#16A34A" />
                    <Text style={styles.plantInfoLabel}>Comestível -</Text>
                    <Text style={styles.plantInfoValue}>Parte: {dadosPlanta.parte_comestivel}</Text>
                  </View>
                ) : null}
                {!!dadosPlanta.forma_uso && (
                  <View style={styles.plantInfoRow}>
                    <Ionicons name="restaurant-outline" size={16} color="#0EA5E9" />
                    <Text style={styles.plantInfoValue}>Uso: {dadosPlanta.forma_uso}</Text>
                  </View>
                )}
                {!!dadosPlanta.epoca_frutificacao && (
                  <View style={styles.plantInfoRow}>
                    <Ionicons name="flower-outline" size={16} color="#D97706" />
                    <Text style={styles.plantInfoValue}>Frutificação: {dadosPlanta.epoca_frutificacao}</Text>
                  </View>
                )}
                {!!dadosPlanta.epoca_colheita && (
                  <View style={styles.plantInfoRow}>
                    <Ionicons name="calendar-outline" size={16} color="#7C3AED" />
                    <Text style={styles.plantInfoValue}>Colheita: {dadosPlanta.epoca_colheita}</Text>
                  </View>
                )}
              </View>
            )}

            {!!resultado.descricao && (
              <Text style={styles.description}>{resultado.descricao}</Text>
            )}

            {/* Meta info */}
            <View style={styles.metaInfo}>
              <View style={styles.metaItem}>
                <Ionicons name="cog-outline" size={14} color="#94A3B8" />
                <Text style={styles.metaText}>{resultado.metodoNome}</Text>
              </View>
              <View style={styles.metaItem}>
                <Ionicons name="timer-outline" size={14} color="#94A3B8" />
                <Text style={styles.metaText}>{resultado.tempoProcessamento}s</Text>
              </View>
            </View>

            {/* Ações do resultado */}
            <View style={styles.resultActions}>
              <TouchableOpacity
                style={styles.resultActionBtn}
                onPress={() => usarEmCadastro(resultado)}
              >
                <Ionicons name="add-circle-outline" size={18} color="#1B9E5A" />
                <Text style={styles.resultActionText}>Usar em Cadastro</Text>
              </TouchableOpacity>
              {resultado.plantaId && (
                <TouchableOpacity
                  style={styles.resultActionBtn}
                  onPress={() => navigation.navigate('DetalhePonto', { id: resultado.plantaId })}
                >
                  <Ionicons name="information-circle-outline" size={18} color="#0EA5E9" />
                  <Text style={[styles.resultActionText, { color: '#0EA5E9' }]}>Ver Detalhes</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </ScrollView>
      )}

      {/* Controles */}
      <View style={[styles.controls, { paddingBottom: Math.max(16, insets.bottom + 8) }]}>
        {!capturedPhoto ? (
          <>
            <TouchableOpacity
              style={[styles.captureButton, !cameraReady && styles.captureButtonDisabled]}
              onPress={tirarFoto}
              disabled={!cameraReady}
            >
              <View style={styles.captureButtonInner} />
            </TouchableOpacity>
            <Text style={styles.hint}>
              Tire uma foto da planta para identificá-la
            </Text>
            <TouchableOpacity
              style={[styles.liveDetectToggle, deteccaoAoVivo && styles.liveDetectToggleActive]}
              onPress={() => setDeteccaoAoVivo((prev) => !prev)}
            >
              <Ionicons name={deteccaoAoVivo ? 'pause' : 'play'} size={16} color="#fff" />
              <Text style={styles.liveDetectText}>{deteccaoAoVivo ? 'Pausar detecção ao vivo' : 'Detecção ao vivo'}</Text>
            </TouchableOpacity>
          </>
        ) : (
          <>
            <View style={styles.modeRow}>
              <TouchableOpacity
                style={styles.modeToggle}
                onPress={() => setModoDeteccao(modoDeteccao === 'assistido' ? 'automatico' : 'assistido')}
              >
                <Ionicons name={modoDeteccao === 'assistido' ? 'hand-left-outline' : 'flash-outline'} size={14} color="#94A3B8" />
                <Text style={styles.modeText}>Modo: {modoDeteccao}</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.actionButtons}>
              <TouchableOpacity style={[styles.actionButton, styles.retryButton]} onPress={resetar}>
                <Ionicons name="refresh" size={18} color="#fff" />
                <Text style={styles.actionButtonText}>Nova</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.autoDetectButton]}
                onPress={detectarAutomaticamente}
                disabled={identifying}
              >
                <Ionicons name="scan-outline" size={18} color="#fff" />
                <Text style={styles.actionButtonText}>Offline</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.identifyButton]}
                onPress={identificarPlanta}
                disabled={identifying}
              >
                {identifying ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <>
                    <Ionicons name="search" size={18} color="#fff" />
                    <Text style={styles.actionButtonText}>Identificar</Text>
                  </>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.actionButton, styles.aiButton]}
                onPress={identificarComIA}
                disabled={identifying}
              >
                {identifying ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <>
                    <Ionicons name="sparkles" size={18} color="#fff" />
                    <Text style={styles.actionButtonText}>IA</Text>
                  </>
                )}
              </TouchableOpacity>
            </View>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  permissionContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  permissionText: {
    color: '#94A3B8',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 16,
    lineHeight: 24,
  },
  permissionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#1B9E5A',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 24,
  },
  permissionBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  permissionBtnSecondary: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 12,
  },
  permissionBtnSecondaryText: { color: '#94A3B8', fontSize: 16, fontWeight: '600' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 12,
    backgroundColor: '#1E293B',
  },
  headerBtn: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: 'rgba(255,255,255,0.1)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    color: '#F1F5F9',
    fontSize: 18,
    fontWeight: '700',
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  cameraFallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    backgroundColor: '#1E293B',
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  targetFrame: {
    width: width * 0.75,
    height: width * 0.75,
    justifyContent: 'center',
    alignItems: 'center',
  },
  targetCorner1: { position: 'absolute', top: 0, left: 0, width: 40, height: 40, borderTopWidth: 3, borderLeftWidth: 3, borderColor: '#1B9E5A', borderTopLeftRadius: 16 },
  targetCorner2: { position: 'absolute', top: 0, right: 0, width: 40, height: 40, borderTopWidth: 3, borderRightWidth: 3, borderColor: '#1B9E5A', borderTopRightRadius: 16 },
  targetCorner3: { position: 'absolute', bottom: 0, left: 0, width: 40, height: 40, borderBottomWidth: 3, borderLeftWidth: 3, borderColor: '#1B9E5A', borderBottomLeftRadius: 16 },
  targetCorner4: { position: 'absolute', bottom: 0, right: 0, width: 40, height: 40, borderBottomWidth: 3, borderRightWidth: 3, borderColor: '#1B9E5A', borderBottomRightRadius: 16 },
  targetText: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 16,
    fontWeight: '600',
  },
  previewContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  preview: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  controls: {
    paddingHorizontal: 20,
    paddingTop: 16,
    backgroundColor: '#1E293B',
    alignItems: 'center',
  },
  captureButton: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#1B9E5A',
  },
  captureButtonDisabled: {
    opacity: 0.4,
  },
  captureButtonInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#1B9E5A',
  },
  hint: {
    color: '#94A3B8',
    fontSize: 13,
    marginTop: 10,
    textAlign: 'center',
  },
  liveDetectToggle: {
    marginTop: 10,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  liveDetectToggleActive: {
    backgroundColor: '#16A34A',
  },
  liveDetectText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 13,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
    width: '100%',
  },
  actionButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'column',
    gap: 4,
  },
  retryButton: {
    backgroundColor: '#475569',
  },
  identifyButton: {
    backgroundColor: '#1B9E5A',
  },
  aiButton: {
    backgroundColor: '#6366F1',
  },
  autoDetectButton: {
    backgroundColor: '#0EA5E9',
  },
  modeRow: {
    marginBottom: 10,
    alignItems: 'center',
  },
  modeToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255,255,255,0.08)',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
  },
  modeText: {
    color: '#94A3B8',
    fontSize: 12,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
  },
  resultContainer: {
    maxHeight: height * 0.45,
    backgroundColor: '#fff',
  },
  resultContent: {
    padding: 0,
  },
  resultCard: {
    padding: 20,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  resultStatus: {
    fontSize: 15,
    fontWeight: '700',
  },
  confidenceBadge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
  },
  highConfidence: {
    backgroundColor: '#DCFCE7',
  },
  mediumConfidence: {
    backgroundColor: '#FEF3C7',
  },
  lowConfidence: {
    backgroundColor: '#FEE2E2',
  },
  confidenceText: {
    fontWeight: '800',
    fontSize: 14,
  },
  plantName: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 4,
  },
  scientificName: {
    fontSize: 15,
    fontStyle: 'italic',
    color: '#94A3B8',
    marginBottom: 12,
  },
  plantInfoSection: {
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    gap: 8,
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  plantInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  plantInfoLabel: {
    color: '#16A34A',
    fontSize: 14,
    fontWeight: '700',
  },
  plantInfoValue: {
    color: '#475569',
    fontSize: 14,
    flex: 1,
  },
  description: {
    fontSize: 14,
    color: '#475569',
    marginBottom: 12,
    lineHeight: 20,
  },
  metaInfo: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    gap: 20,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 12,
    color: '#94A3B8',
  },
  resultActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  resultActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#F0FDF4',
  },
  resultActionText: {
    color: '#1B9E5A',
    fontWeight: '700',
    fontSize: 13,
  },
  errorText: {
    color: '#94A3B8',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 12,
  },
});
