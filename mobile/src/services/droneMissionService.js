import { OFFLINE_KEYS, upsertCollection } from './offlineStorage';

class DroneMissionService {
  async registrarMissao({ missionId, operador, area, trilha = [], sensores = {} }) {
    const missao = {
      mission_id: missionId,
      operador,
      area,
      trilha_voo: trilha,
      sensores,
      status: 'coletada_offline',
      criado_em: new Date().toISOString(),
    };

    await upsertCollection(OFFLINE_KEYS.DRONE_MISSIONS, [missao], 'mission_id');
    return missao;
  }

  async registrarLoteCaptura({ missionId, imagens = [], pontos = [] }) {
    const lote = {
      id: `batch_${Date.now()}`,
      mission_id: missionId,
      imagens,
      pontos,
      status_sync: 'pendente',
      criado_em: new Date().toISOString(),
    };

    await upsertCollection(OFFLINE_KEYS.DRONE_MISSIONS, [lote], 'id');
    return lote;
  }
}

export default new DroneMissionService();
