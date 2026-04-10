import { OFFLINE_KEYS, upsertCollection } from './offlineStorage';
import AsyncStorage from '@react-native-async-storage/async-storage';

const AI_MODEL_VERSION = 'heuristic-offline-v1';

const scoreByText = (input, candidates) => {
  const normalized = (input || '').toLowerCase();
  return candidates.map((species) => {
    const keys = [species.nome_cientifico, ...(species.nomes_populares || [])]
      .join(' ')
      .toLowerCase();
    const overlap = normalized && keys.includes(normalized) ? 0.9 : 0.55;
    const prioridade = species.regra_prioridade === 'alta' ? 0.15 : 0;
    const confidence = Math.min(0.98, overlap + prioridade);
    return { species, confidence };
  }).sort((a, b) => b.confidence - a.confidence);
};

class AiAssistService {
  async sugerirCadastro({ observacaoTexto, localizacao, imagemUri, origem = 'mobile_campo' }) {
    const species = JSON.parse(await AsyncStorage.getItem(OFFLINE_KEYS.SPECIES_FOCUS) || '[]');
    if (!species.length) {
      return { sucesso: false, erro: 'Base local de espécies foco vazia' };
    }

    const ranking = scoreByText(observacaoTexto, species);
    const melhor = ranking[0];

    const inferencia = {
      id: `ai_${Date.now()}`,
      model_version: AI_MODEL_VERSION,
      origem_coleta: origem,
      timestamp: new Date().toISOString(),
      coordenada: localizacao || null,
      imagem_uri: imagemUri || null,
      especie_sugerida_id: melhor?.species?.id || null,
      especie_sugerida: melhor?.species?.nome_cientifico || null,
      confianca: Number(melhor?.confidence || 0),
      status_revisao_humana: 'pendente',
    };

    await upsertCollection(OFFLINE_KEYS.IA_HISTORY, [inferencia]);

    return {
      sucesso: true,
      inferencia,
      preCadastro: {
        nome_cientifico: melhor?.species?.nome_cientifico || '',
        nome_popular: melhor?.species?.nomes_populares?.[0] || '',
        status_validacao: 'pendente_revisao_humana',
        confianca_ia: inferencia.confianca,
      },
    };
  }
}

export default new AiAssistService();
