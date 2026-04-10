import * as Location from 'expo-location';
import aiAssistService from './aiAssistService';
import offlineService from './offlineService';
import { adicionarPontoDetectadoCache, salvarHistoricoDeteccao } from './offlineStorage';

const CONFIDENCE_STRONG = 0.8;
const CONFIDENCE_PROBABLE = 0.65;
const DETECTION_COOLDOWN_MS = 25000;

class AutoDetectionService {
  constructor() {
    this.lastDetectionAt = 0;
    this.lastDetectionKey = null;
  }

  classificarConfianca(value) {
    if (value >= CONFIDENCE_STRONG) return 'deteccao_forte';
    if (value >= CONFIDENCE_PROBABLE) return 'deteccao_provavel';
    return 'necessita_revisao';
  }

  async obterLocalizacao() {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') return null;
      const loc = await Location.getCurrentPositionAsync({});
      return [loc.coords.longitude, loc.coords.latitude];
    } catch (error) {
      console.warn('[AUTO_DETECTION] Falha ao obter localização', error?.message || error);
      return null;
    }
  }

  async processarDeteccaoAutomatica({ imageUri, observacao = '', usuarioId = null, modo = 'assistido' }) {
    const now = Date.now();
    if (now - this.lastDetectionAt < DETECTION_COOLDOWN_MS) {
      return { sucesso: false, ignorado: true, motivo: 'cooldown_ativo' };
    }

    const localizacao = await this.obterLocalizacao();
    const ia = await aiAssistService.sugerirCadastro({
      observacaoTexto: observacao,
      localizacao,
      imagemUri: imageUri,
      origem: `camera_${modo}`,
    });

    if (!ia.sucesso) return ia;

    const confidence = Number(ia.inferencia.confianca || 0);
    const statusDeteccao = this.classificarConfianca(confidence);
    const locationKey = localizacao
      ? `${Number(localizacao[0]).toFixed(4)},${Number(localizacao[1]).toFixed(4)}`
      : 'sem_local';
    const detectionKey = `${ia.inferencia.especie_sugerida_id}:${locationKey}`;
    if (this.lastDetectionKey === detectionKey && now - this.lastDetectionAt < DETECTION_COOLDOWN_MS * 2) {
      return { sucesso: false, ignorado: true, motivo: 'duplicidade_temporal' };
    }

    const payload = {
      nome_popular: ia.preCadastro.nome_popular,
      nome_cientifico: ia.preCadastro.nome_cientifico,
      tipo_local: 'deteccao_automatica_mobile',
      relato: JSON.stringify({
        origem_cadastro: 'detecao_automatica_mobile',
        usuario_id: usuarioId,
        confidence,
        status_deteccao: statusDeteccao,
        inferencia_id: ia.inferencia.id,
        model_version: ia.inferencia.model_version,
        offline_base: true,
        revisao_humana: 'pendente',
      }),
      localizacao,
      foto_uri: imageUri,
      status_validacao: 'pendente',
      status_fluxo: 'submetido',
    };

    const registro = await offlineService.registrarPonto(payload);

    const pontoLocal = {
      id_temporario: registro.item?.id_temporario || `det_${Date.now()}`,
      nome_popular: payload.nome_popular,
      nome_cientifico: payload.nome_cientifico,
      localizacao,
      status_validacao: 'pendente',
      status_deteccao: statusDeteccao,
      status_sync: registro.origem === 'offline' ? 'aguardando_sincronizacao' : 'sincronizado',
      confianca_ia: confidence,
      criado_em: new Date().toISOString(),
      foto_url: imageUri,
    };

    await adicionarPontoDetectadoCache(pontoLocal);
    await salvarHistoricoDeteccao({
      ...ia.inferencia,
      status_deteccao: statusDeteccao,
      status_sync: pontoLocal.status_sync,
      ponto_local_id: pontoLocal.id_temporario,
    });

    this.lastDetectionAt = now;
    this.lastDetectionKey = detectionKey;

    return {
      sucesso: true,
      statusDeteccao,
      confianca: confidence,
      pontoLocal,
      registro,
      inferencia: ia.inferencia,
    };
  }
}

export default new AutoDetectionService();
