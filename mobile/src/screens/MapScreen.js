import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Dimensions } from 'react-native';
import MapView, { Marker, Callout, PROVIDER_DEFAULT } from 'react-native-maps';
import offlineService from '../services/offlineService';
import { normalizeEnrichmentData } from '../utils/enrichmentStatus';

const toCoords = (localizacao) => {
  if (!localizacao) return null;
  if (Array.isArray(localizacao) && localizacao.length === 2) {
    return { latitude: Number(localizacao[1]), longitude: Number(localizacao[0]) };
  }
  if (localizacao?.coordinates?.length === 2) {
    return { latitude: Number(localizacao.coordinates[1]), longitude: Number(localizacao.coordinates[0]) };
  }
  return null;
};

const getPontoResumo = (ponto) => {
  const planta = ponto?.planta || {};
  const enrichment = normalizeEnrichmentData(ponto || {});
  return {
    nomePopular: ponto?.nome_popular || planta?.nome_popular || 'Ponto não identificado',
    nomeCientifico: ponto?.nome_cientifico || planta?.nome_cientifico || '',
    cidade: ponto?.cidade || '',
    estado: ponto?.estado || '',
    tipoLocal: ponto?.tipo_local || ponto?.descricao_local || '',
    descricao: ponto?.descricao || ponto?.observacoes || '',
    formaUso: ponto?.forma_uso || planta?.forma_uso || '',
    statusValidacao: ponto?.status_validacao || 'pendente',
    enrichment,
  };
};

export default function MapScreen({ navigation }) {
  const [pontos, setPontos] = useState([]);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    let ativo = true;
    const carregarDados = async () => {
      try {
        const resultado = await offlineService.buscarPontos({ usarPreviewMapa: true });
        if (ativo) setPontos(Array.isArray(resultado.dados) ? resultado.dados : []);
      } finally {
        if (ativo) setCarregando(false);
      }
    };

    carregarDados();
    return () => { ativo = false; };
  }, []);

  if (carregando) return <ActivityIndicator style={{ marginTop: 50 }} color="#1B9E5A" size="large" />;

  const corMarcador = (status) => {
    if (status === 'aprovado') return '#1B9E5A';
    if (status === 'reprovado') return '#E53E3E';
    return '#EAB308';
  };

  return (
    <View style={styles.container}>
      <MapView provider={PROVIDER_DEFAULT} style={styles.map} initialRegion={{ latitude: -14.2, longitude: -51.9, latitudeDelta: 25, longitudeDelta: 25 }}>
        {pontos.map((ponto) => {
          const coords = toCoords(ponto.localizacao);
          if (!coords) return null;
          const resumo = getPontoResumo(ponto);

          return (
            <Marker key={ponto.id || ponto.id_temporario} coordinate={coords} pinColor={corMarcador(ponto.status_validacao)}>
              <Callout onPress={() => ponto.id && navigation.navigate('DetalhePonto', { id: ponto.id })}>
                <View style={styles.popup}>
                  <Text style={styles.titulo}>{resumo.nomePopular}</Text>
                  {!!resumo.nomeCientifico && <Text style={styles.cientifico}>{resumo.nomeCientifico}</Text>}

                  <Text style={styles.infoText}>{resumo.cidade || '-'} / {resumo.estado || '-'}</Text>
                  {!!resumo.tipoLocal && <Text style={styles.infoText}>Local: {resumo.tipoLocal}</Text>}
                  <Text style={styles.infoText}>Validação: {resumo.statusValidacao}</Text>

                  {resumo.enrichment.comestibilidade_confirmada && <Text style={styles.infoText}>Comestível: {resumo.enrichment.comestibilidade_label}</Text>}
                  {resumo.enrichment.parte_comestivel_confirmada && <Text style={styles.infoText}>Parte: {resumo.enrichment.parte_comestivel}</Text>}
                  {resumo.enrichment.frutificacao_confirmada && <Text style={styles.infoText}>Frutificação: {resumo.enrichment.frutificacao_meses}</Text>}
                  {resumo.enrichment.colheita_confirmada && <Text style={styles.infoText}>Colheita: {resumo.enrichment.colheita_periodo}</Text>}

                  {!!resumo.formaUso && <Text style={styles.infoText} numberOfLines={1}>Uso: {resumo.formaUso}</Text>}
                  {!!resumo.descricao && <Text style={styles.descricao} numberOfLines={2}>{resumo.descricao}</Text>}

                  <Text style={styles.linkHint}>Toque para ver detalhes</Text>
                </View>
              </Callout>
            </Marker>
          );
        })}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0FDF4' },
  map: { width: Dimensions.get('window').width, height: Dimensions.get('window').height },
  popup: {
    minWidth: 220,
    maxWidth: 280,
    padding: 10,
  },
  titulo: { fontWeight: '700', fontSize: 15, color: '#1B9E5A', marginBottom: 2 },
  cientifico: { color: '#94A3B8', fontSize: 12, fontStyle: 'italic', marginBottom: 4 },
  infoText: { color: '#475569', fontSize: 12, marginTop: 2 },
  descricao: { color: '#64748B', fontSize: 11, marginTop: 4, fontStyle: 'italic' },
  linkHint: { color: '#1B9E5A', fontSize: 11, fontWeight: '600', marginTop: 6, textAlign: 'center' },
});
