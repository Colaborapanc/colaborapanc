import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Image, ActivityIndicator, ScrollView, TouchableOpacity, Linking, Alert } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { API_ENDPOINTS, buildURL } from '../config/api';
import { carregarPontosCache } from '../services/offlineStorage';
import enrichmentService from '../services/enrichmentService';
import { consultarEnriquecimento, calcularSeloValidacao, SELO_CONFIG } from '../services/enriquecimentoService';
import {
  getEnrichmentStatusUI,
  getFallbackEnrichmentText,
  normalizeEnrichmentData,
} from '../utils/enrichmentStatus';

const InfoCard = ({ icon, iconColor, label, value, highlight }) => {
  if (!value) return null;
  return (
    <View style={styles.infoCard}>
      <View style={styles.infoCardIcon}>
        <Ionicons name={icon} size={20} color={iconColor || '#64748B'} />
      </View>
      <View style={styles.infoCardContent}>
        <Text style={styles.infoCardLabel}>{label}</Text>
        <Text style={[styles.infoCardValue, highlight && { color: iconColor, fontWeight: '700' }]}>{value}</Text>
      </View>
    </View>
  );
};

const SectionHeader = ({ icon, iconColor, title }) => (
  <View style={styles.sectionHeader}>
    <Ionicons name={icon} size={20} color={iconColor || '#1B9E5A'} />
    <Text style={[styles.sectionTitle, { color: iconColor || '#1B9E5A' }]}>{title}</Text>
  </View>
);

export default function DetalhePontoScreen({ route, navigation }) {
  const { id } = route.params;
  const insets = useSafeAreaInsets();
  const [ponto, setPonto] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [enriquecimento, setEnriquecimento] = useState(null);
  const [enriquecimentoLoading, setEnriquecimentoLoading] = useState(false);
  const [revalidando, setRevalidando] = useState(false);

  const extrairCoordenadas = (localizacao) => {
    if (!localizacao) return null;
    if (Array.isArray(localizacao) && localizacao.length === 2) {
      return { longitude: Number(localizacao[0]), latitude: Number(localizacao[1]) };
    }
    if (Array.isArray(localizacao?.coordinates) && localizacao.coordinates.length === 2) {
      return { longitude: Number(localizacao.coordinates[0]), latitude: Number(localizacao.coordinates[1]) };
    }
    if (typeof localizacao?.longitude !== 'undefined' && typeof localizacao?.latitude !== 'undefined') {
      return { longitude: Number(localizacao.longitude), latitude: Number(localizacao.latitude) };
    }
    return null;
  };

  const abrirNavegacao = async () => {
    const coords = extrairCoordenadas(ponto?.localizacao);
    if (!coords) {
      Alert.alert('Localização indisponível', 'Este ponto não possui coordenadas válidas.');
      return;
    }
    const latitude = Number(coords.latitude);
    const longitude = Number(coords.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      Alert.alert('Localização inválida', 'As coordenadas deste ponto estão inválidas.');
      return;
    }
    const googleMapsUrl = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
    const wazeUrl = `https://waze.com/ul?ll=${latitude},${longitude}&navigate=yes`;
    const wazeDisponivel = await Linking.canOpenURL(wazeUrl);
    await Linking.openURL(wazeDisponivel ? wazeUrl : googleMapsUrl);
  };

  useEffect(() => {
    let ativo = true;

    const carregarDetalhe = async () => {
      const pontoId = Number(id);
      try {
        const cache = await carregarPontosCache();
        const encontrado = Array.isArray(cache)
          ? cache.find((item) => item.id === pontoId)
          : null;
        if (ativo && encontrado) setPonto(encontrado);
      } catch (error) {
        // segue para busca remota
      }

      try {
        const data = await enrichmentService.carregarPonto(pontoId);
        if (ativo) setPonto(data);
      } catch (error) {
        const cache = await carregarPontosCache();
        const encontrado = Array.isArray(cache) ? cache.find((item) => item.id === pontoId) : null;
        if (ativo && !ponto) setPonto(encontrado || null);
      } finally {
        if (ativo) setCarregando(false);
      }
    };

    carregarDetalhe();
    return () => { ativo = false; };
  }, [id]);

  // Carregar enriquecimento quando ponto estiver disponível
  useEffect(() => {
    if (!ponto) return;
    // Tentar dos dados inline primeiro (API já retorna enriquecimento no serializer)
    if (ponto.enriquecimento && ponto.enriquecimento.status_enriquecimento !== 'pendente') {
      setEnriquecimento(ponto.enriquecimento);
      return;
    }
    // Fallback: buscar do endpoint dedicado se temos planta_id
    const plantaId = ponto.planta_id || ponto.planta?.id;
    if (!plantaId) return;
    let ativo = true;
    setEnriquecimentoLoading(true);
    consultarEnriquecimento(plantaId)
      .then((res) => {
        if (ativo && res.sucesso && res.dados && res.dados.status_enriquecimento !== 'pendente') {
          setEnriquecimento(res.dados);
        }
      })
      .catch(() => {})
      .finally(() => { if (ativo) setEnriquecimentoLoading(false); });
    return () => { ativo = false; };
  }, [ponto]);

  if (carregando) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1B9E5A" />
        <Text style={styles.loadingText}>Carregando detalhes...</Text>
      </View>
    );
  }

  if (!ponto) {
    return (
      <View style={styles.center}>
        <Ionicons name="alert-circle-outline" size={48} color="#94A3B8" />
        <Text style={styles.emptyText}>Ponto não encontrado.</Text>
        <TouchableOpacity style={styles.btnVoltar} onPress={() => navigation.goBack()}>
          <Text style={styles.btnVoltarText}>Voltar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const planta = ponto.planta || {};
  const formaUso = ponto.forma_uso || planta.forma_uso || '';
  const grupoTaxonomico = planta.grupo_taxonomico || '';
  const bioma = planta.bioma || '';
  const origem = planta.origem || '';

  const statusLabel = ponto.status_validacao === 'aprovado' ? 'Aprovado'
    : ponto.status_validacao === 'reprovado' ? 'Reprovado' : 'Pendente';
  const statusColor = ponto.status_validacao === 'aprovado' ? '#16A34A'
    : ponto.status_validacao === 'reprovado' ? '#DC2626' : '#EAB308';
  const enrichment = normalizeEnrichmentData({ ...ponto, ...(enriquecimento || {}) });
  const enrichmentUI = getEnrichmentStatusUI(enrichment.status_enriquecimento);
  const seloLabel = enrichmentUI.label;
  const enrichmentFallbackText = getFallbackEnrichmentText(enrichment.status_enriquecimento);

  const revalidarDados = async () => {
    setRevalidando(true);
    try {
      await enrichmentService.revalidarPonto(id);
      const atualizado = await enrichmentService.carregarPonto(id);
      setPonto(atualizado);
      Alert.alert('Revalidação iniciada', 'Dados de validação atualizados com sucesso.');
    } catch (error) {
      Alert.alert('Erro', 'Não foi possível revalidar agora. Tente novamente em instantes.');
    } finally {
      setRevalidando(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.scrollView} contentContainerStyle={{ paddingBottom: Math.max(24, insets.bottom + 16) }}>
        {/* Header com foto */}
        {ponto.foto_url ? (
          <View style={styles.fotoContainer}>
            <Image source={{ uri: ponto.foto_url }} style={styles.foto} />
            <View style={styles.fotoOverlay}>
              <TouchableOpacity style={styles.btnBackFloat} onPress={() => navigation.goBack()}>
                <Ionicons name="arrow-back" size={22} color="#fff" />
              </TouchableOpacity>
              <View style={[styles.statusBadge, { backgroundColor: statusColor }]}>
                <Text style={styles.statusBadgeText}>{statusLabel}</Text>
              </View>
            </View>
          </View>
        ) : (
          <View style={styles.headerNoFoto}>
            <TouchableOpacity style={styles.btnBackNoFoto} onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={22} color="#1B9E5A" />
            </TouchableOpacity>
            <View style={[styles.statusBadge, { backgroundColor: statusColor }]}>
              <Text style={styles.statusBadgeText}>{statusLabel}</Text>
            </View>
          </View>
        )}

        {/* Nome */}
        <View style={styles.content}>
          <Text style={styles.titulo}>{ponto.nome_popular || 'Ponto não identificado'}</Text>
          {!!ponto.nome_cientifico && (
            <Text style={styles.cientifico}>{ponto.nome_cientifico}</Text>
          )}

          {/* Score de identificação */}
          {ponto.score_identificacao > 0 && (
            <View style={styles.scoreRow}>
              <View style={[styles.scoreBadge, {
                backgroundColor: ponto.score_identificacao >= 70 ? '#DCFCE7' : ponto.score_identificacao >= 50 ? '#FEF3C7' : '#FEE2E2'
              }]}>
                <Ionicons name="analytics" size={14} color={ponto.score_identificacao >= 70 ? '#16A34A' : ponto.score_identificacao >= 50 ? '#D97706' : '#DC2626'} />
                <Text style={[styles.scoreText, {
                  color: ponto.score_identificacao >= 70 ? '#16A34A' : ponto.score_identificacao >= 50 ? '#D97706' : '#DC2626'
                }]}>Confiança: {Math.round(ponto.score_identificacao)}%</Text>
              </View>
            </View>
          )}

          {/* Seção: Uso alimentar e fenologia */}
          <View style={styles.section}>
            <SectionHeader icon="nutrition" iconColor="#16A34A" title="Uso alimentar e fenologia" />
            <View style={styles.comestibilidadeCard}>
              {enrichment.comestibilidade_confirmada && (
                <View style={styles.detailRow}>
                  <Ionicons name="checkmark-done-outline" size={16} color="#16A34A" />
                  <Text style={styles.detailLabel}>Comestível (integração):</Text>
                  <Text style={styles.detailValue}>{enrichment.comestibilidade_label}</Text>
                </View>
              )}
              {enrichment.parte_comestivel_confirmada && (
                <View style={styles.detailRow}>
                  <Ionicons name="leaf-outline" size={16} color="#16A34A" />
                  <Text style={styles.detailLabel}>Parte comestível:</Text>
                  <Text style={styles.detailValue}>{enrichment.parte_comestivel}</Text>
                </View>
              )}
              {enrichment.frutificacao_confirmada && (
                <View style={styles.detailRow}>
                  <Ionicons name="flower-outline" size={16} color="#D97706" />
                  <Text style={styles.detailLabel}>Frutificação:</Text>
                  <Text style={styles.detailValue}>{enrichment.frutificacao_meses}</Text>
                </View>
              )}
              {enrichment.colheita_confirmada && (
                <View style={styles.detailRow}>
                  <Ionicons name="basket-outline" size={16} color="#7C3AED" />
                  <Text style={styles.detailLabel}>Colheita:</Text>
                  <Text style={styles.detailValue}>{enrichment.colheita_periodo}</Text>
                </View>
              )}
              {(!enrichment.comestibilidade_confirmada && !enrichment.parte_comestivel_confirmada && !enrichment.frutificacao_confirmada && !enrichment.colheita_confirmada) && (
                <Text style={styles.fallbackText}>Campos alimentares ocultados por ausência de evidência suficiente.</Text>
              )}
              {!!formaUso && (
                <View style={styles.detailRow}>
                  <Ionicons name="restaurant-outline" size={16} color="#0EA5E9" />
                  <Text style={styles.detailLabel}>Forma de uso:</Text>
                  <Text style={styles.detailValue}>{formaUso}</Text>
                </View>
              )}
            </View>
          </View>

          {/* Seção: Localização */}
          <View style={styles.section}>
            <SectionHeader icon="location" iconColor="#0EA5E9" title="Localização" />
            <InfoCard icon="location-outline" iconColor="#0EA5E9" label="Cidade/Estado" value={`${ponto.cidade || '-'} / ${ponto.estado || '-'}`} />
            <InfoCard icon="home-outline" iconColor="#64748B" label="Tipo de local" value={ponto.tipo_local} />
            <InfoCard icon="person-outline" iconColor="#8B5CF6" label="Colaborador" value={ponto.colaborador} />
          </View>

          {/* Seção: Classificação */}
          {(!!grupoTaxonomico || !!bioma || !!origem) && (
            <View style={styles.section}>
              <SectionHeader icon="flask" iconColor="#8B5CF6" title="Classificação" />
              <InfoCard icon="git-branch-outline" iconColor="#8B5CF6" label="Grupo taxonômico" value={grupoTaxonomico} />
              <InfoCard icon="earth-outline" iconColor="#059669" label="Bioma" value={bioma} />
              <InfoCard icon="globe-outline" iconColor="#0EA5E9" label="Origem" value={origem} />
            </View>
          )}

          {/* Seção: Enriquecimento Taxonômico */}
          {enriquecimento ? (() => {
            const selo = calcularSeloValidacao(enriquecimento);
            const seloConf = SELO_CONFIG[selo];
            return (
              <View style={styles.section}>
                <View style={styles.sectionHeader}>
                  <Ionicons name="search" size={20} color="#0EA5E9" />
                  <Text style={[styles.sectionTitle, { color: '#0EA5E9' }]}>Enriquecimento Taxonômico</Text>
                  <View style={[styles.seloBadge, { backgroundColor: seloConf.bgColor }]}>
                    <Ionicons name={seloConf.icon} size={14} color={seloConf.color} />
                    <Text style={[styles.seloText, { color: seloConf.color }]}>{seloConf.label}</Text>
                  </View>
                </View>

                {!!enriquecimento.nome_cientifico_validado && (
                  <InfoCard icon="checkmark-done" iconColor="#16A34A" label="Nome validado" value={enriquecimento.nome_cientifico_validado} />
                )}
                {!!enriquecimento.nome_aceito && (
                  <InfoCard icon="ribbon" iconColor="#7C3AED" label="Nome aceito" value={enriquecimento.nome_aceito} highlight />
                )}
                {!!enriquecimento.autoria && (
                  <InfoCard icon="person" iconColor="#64748B" label="Autoria" value={enriquecimento.autoria} />
                )}
                {!!enriquecimento.fonte_taxonomica_primaria && (
                  <InfoCard icon="library" iconColor="#0EA5E9" label="Fonte primária" value={enriquecimento.fonte_taxonomica_primaria} />
                )}

                {enrichment.grau_confianca_taxonomica != null && (
                  <View style={styles.confiancaContainer}>
                    <Text style={styles.confiancaLabel}>Grau de confiança</Text>
                    <View style={styles.progressBarBg}>
                      <View style={[styles.progressBarFill, {
                        width: `${Math.round(enrichment.grau_confianca_taxonomica * 100)}%`,
                        backgroundColor: enrichment.grau_confianca_taxonomica >= 0.7 ? '#16A34A' : enrichment.grau_confianca_taxonomica >= 0.4 ? '#EAB308' : '#DC2626',
                      }]} />
                    </View>
                    <Text style={styles.confiancaValue}>{Math.round(enrichment.grau_confianca_taxonomica * 100)}%</Text>
                  </View>
                )}

                {/* Ocorrências */}
                <View style={styles.occRow}>
                  {enriquecimento.ocorrencias_gbif != null && (
                    <View style={styles.occCard}>
                      <Text style={[styles.occNumber, { color: '#16A34A' }]}>{enriquecimento.ocorrencias_gbif.toLocaleString()}</Text>
                      <Text style={styles.occLabel}>GBIF</Text>
                    </View>
                  )}
                  {enriquecimento.ocorrencias_inaturalist != null && (
                    <View style={styles.occCard}>
                      <Text style={[styles.occNumber, { color: '#0EA5E9' }]}>{enriquecimento.ocorrencias_inaturalist.toLocaleString()}</Text>
                      <Text style={styles.occLabel}>iNaturalist</Text>
                    </View>
                  )}
                </View>

                {/* Sinônimos */}
                {Array.isArray(enriquecimento.sinonimos) && enriquecimento.sinonimos.length > 0 && (
                  <View style={styles.sinonimoContainer}>
                    <Text style={styles.sinonimoTitle}>Sinônimos</Text>
                    <View style={styles.sinonimoWrap}>
                      {enriquecimento.sinonimos.slice(0, 8).map((s, i) => (
                        <View key={i} style={styles.sinonimoBadge}>
                          <Text style={styles.sinonimoText}>{s}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                )}

                {/* Fenologia */}
                {enriquecimento.fenologia_observada && enriquecimento.fenologia_observada.meses && Object.keys(enriquecimento.fenologia_observada.meses).length > 0 && (
                  <View style={styles.fenologiaContainer}>
                    <Text style={styles.sinonimoTitle}>Fenologia (iNaturalist)</Text>
                    <View style={styles.sinonimoWrap}>
                      {Object.entries(enriquecimento.fenologia_observada.meses).map(([mes, qtd]) => (
                        <View key={mes} style={[styles.sinonimoBadge, { backgroundColor: '#DCFCE7' }]}>
                          <Text style={[styles.sinonimoText, { color: '#16A34A' }]}>{mes}: {qtd}</Text>
                        </View>
                      ))}
                    </View>
                    {!!enriquecimento.fenologia_observada.estacao_pico && (
                      <Text style={styles.fenologiaPico}>Pico: {enriquecimento.fenologia_observada.estacao_pico}</Text>
                    )}
                  </View>
                )}

                {/* Imagem de referência */}
                {!!enriquecimento.imagem_url && (
                  <View style={styles.refImageContainer}>
                    <Image source={{ uri: enriquecimento.imagem_url }} style={styles.refImage} />
                    {!!enriquecimento.imagem_fonte && (
                      <Text style={styles.refImageCaption}>{enriquecimento.imagem_fonte}</Text>
                    )}
                    {!!enriquecimento.licenca_imagem && (
                      <Text style={styles.refImageLicense}>{enriquecimento.licenca_imagem}</Text>
                    )}
                  </View>
                )}

                {!!enriquecimento.ultima_validacao_em && (
                  <Text style={styles.lastValidation}>
                    Última validação: {new Date(enriquecimento.ultima_validacao_em).toLocaleDateString('pt-BR')}
                  </Text>
                )}
              </View>
            );
          })() : enriquecimentoLoading ? (
            <View style={styles.section}>
              <SectionHeader icon="search" iconColor="#0EA5E9" title="Enriquecimento Taxonômico" />
              <View style={{ alignItems: 'center', paddingVertical: 16 }}>
                <ActivityIndicator size="small" color="#0EA5E9" />
                <Text style={{ color: '#94A3B8', marginTop: 8, fontSize: 13 }}>Carregando dados taxonômicos...</Text>
              </View>
            </View>
          ) : null}

          {/* Relato */}
          {!!ponto.relato && (
            <View style={styles.section}>
              <SectionHeader icon="chatbubble-ellipses" iconColor="#64748B" title="Relato" />
              <View style={styles.relatoCard}>
                <Ionicons name="chatbubble-outline" size={16} color="#94A3B8" style={{ marginTop: 2 }} />
                <Text style={styles.relatoText}>"{ponto.relato}"</Text>
              </View>
            </View>
          )}

          {/* Alertas */}
          <View style={styles.section}>
            <SectionHeader icon="warning" iconColor="#EA580C" title="Alertas Climáticos" />
            {Array.isArray(ponto.alertas) && ponto.alertas.length > 0 ? (
              ponto.alertas.map((alerta, idx) => (
                <View key={idx} style={styles.alertaBloco}>
                  <View style={styles.alertaHeader}>
                    <Ionicons name="warning-outline" size={18} color="#EA580C" />
                    <Text style={styles.alertaTipo}>{alerta.tipo}</Text>
                    <View style={[styles.severidadeBadge, {
                      backgroundColor: alerta.severidade === 'alta' ? '#FEE2E2' : alerta.severidade === 'media' ? '#FEF3C7' : '#F0FDF4'
                    }]}>
                      <Text style={[styles.severidadeText, {
                        color: alerta.severidade === 'alta' ? '#DC2626' : alerta.severidade === 'media' ? '#D97706' : '#16A34A'
                      }]}>{alerta.severidade}</Text>
                    </View>
                  </View>
                  <Text style={styles.alertaInfo}>
                    {alerta.inicio ? new Date(alerta.inicio).toLocaleString('pt-BR') : ''}
                    {alerta.fim ? ' a ' + new Date(alerta.fim).toLocaleString('pt-BR') : ''}
                    {alerta.fonte ? ` | ${alerta.fonte}` : ''}
                  </Text>
                  {!!alerta.descricao && <Text style={styles.alertaDesc}>{alerta.descricao}</Text>}
                </View>
              ))
            ) : (
              <View style={styles.alertaVazio}>
                <Ionicons name="checkmark-circle-outline" size={20} color="#16A34A" />
                <Text style={styles.alertaVazioText}>Nenhum alerta registrado para este ponto.</Text>
              </View>
            )}
            <TouchableOpacity
              style={styles.btnHistorico}
              onPress={() => Linking.openURL(buildURL(`/alertas/?ponto=${ponto.id}`))}
            >
              <Ionicons name="time-outline" size={17} color="#fff" />
              <Text style={styles.btnHistoricoTxt}>Ver histórico completo</Text>
            </TouchableOpacity>
          </View>

          {/* Botões de ação */}
          <View style={styles.actionsContainer}>
            <TouchableOpacity style={[styles.btnAcaoSecundario, revalidando && { opacity: 0.6 }]} onPress={revalidarDados} disabled={revalidando}>
              <Ionicons name="refresh" size={20} color="#1B9E5A" />
              <Text style={styles.btnAcaoSecundarioText}>{revalidando ? 'Revalidando...' : 'Revalidar dados'}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.btnAcaoPrimario} onPress={abrirNavegacao}>
              <Ionicons name="navigate" size={20} color="#fff" />
              <Text style={styles.btnAcaoPrimarioText}>Ir ao local</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.btnAcaoSecundario} onPress={() => navigation.navigate('Mapa')}>
              <Ionicons name="map-outline" size={20} color="#1B9E5A" />
              <Text style={styles.btnAcaoSecundarioText}>Voltar ao Mapa</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#F8FAFC' },
  scrollView: { flex: 1 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F8FAFC' },
  loadingText: { marginTop: 12, color: '#64748B', fontSize: 15 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20, backgroundColor: '#F8FAFC' },
  emptyText: { color: '#64748B', fontSize: 16, marginTop: 12 },
  btnVoltar: { marginTop: 16, paddingHorizontal: 24, paddingVertical: 10, backgroundColor: '#1B9E5A', borderRadius: 10 },
  btnVoltarText: { color: '#fff', fontWeight: '600' },

  fotoContainer: { position: 'relative' },
  foto: { width: '100%', height: 260, backgroundColor: '#E2E8F0' },
  fotoOverlay: { position: 'absolute', top: 0, left: 0, right: 0, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', padding: 16 },
  btnBackFloat: { width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'center', alignItems: 'center' },
  headerNoFoto: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, backgroundColor: '#F0FDF4' },
  btnBackNoFoto: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#DCFCE7', justifyContent: 'center', alignItems: 'center' },
  statusBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 },
  statusBadgeText: { color: '#fff', fontSize: 12, fontWeight: '700', textTransform: 'uppercase' },

  content: { padding: 20 },
  titulo: { fontWeight: '800', fontSize: 24, color: '#0F172A', marginBottom: 4 },
  cientifico: { color: '#94A3B8', fontSize: 16, fontStyle: 'italic', marginBottom: 8 },

  scoreRow: { flexDirection: 'row', marginBottom: 8 },
  scoreBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 },
  scoreText: { fontSize: 13, fontWeight: '700' },

  section: { marginTop: 24 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  sectionTitle: { fontSize: 17, fontWeight: '700' },

  comestibilidadeCard: { backgroundColor: '#F0FDF4', borderRadius: 14, padding: 16, borderWidth: 1, borderColor: '#BBF7D0' },
  comestivelRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  comestivelText: { fontSize: 17, fontWeight: '700' },
  detailRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 6 },
  detailLabel: { color: '#64748B', fontSize: 14 },
  detailValue: { color: '#0F172A', fontSize: 14, fontWeight: '600', flex: 1 },

  epocaContainer: { flexDirection: 'row', gap: 12 },
  epocaCard: { flex: 1, backgroundColor: '#FFFBEB', borderRadius: 14, padding: 16, alignItems: 'center', borderWidth: 1, borderColor: '#FDE68A' },
  epocaLabel: { color: '#92400E', fontSize: 12, fontWeight: '600', marginTop: 8 },
  epocaValue: { color: '#78350F', fontSize: 14, fontWeight: '700', marginTop: 4, textAlign: 'center' },

  infoCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderRadius: 12, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#F1F5F9' },
  infoCardIcon: { width: 36, height: 36, borderRadius: 10, backgroundColor: '#F8FAFC', justifyContent: 'center', alignItems: 'center', marginRight: 12 },
  infoCardContent: { flex: 1 },
  infoCardLabel: { color: '#94A3B8', fontSize: 12, marginBottom: 2 },
  infoCardValue: { color: '#0F172A', fontSize: 15, fontWeight: '600' },
  fallbackText: { marginTop: 8, color: '#64748B', fontSize: 13, lineHeight: 18 },
  fallbackWarning: { marginBottom: 8, color: '#B45309', fontSize: 13, fontWeight: '600' },
  revalidateBtn: { marginTop: 12, alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#ECFDF5', borderWidth: 1, borderColor: '#A7F3D0', borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8 },
  revalidateBtnText: { color: '#0F766E', fontWeight: '700', fontSize: 13 },

  relatoCard: { flexDirection: 'row', backgroundColor: '#F8FAFC', borderRadius: 14, padding: 16, gap: 10, borderWidth: 1, borderColor: '#E2E8F0' },
  relatoText: { color: '#475569', fontSize: 15, fontStyle: 'italic', flex: 1, lineHeight: 22 },

  alertaBloco: { backgroundColor: '#FFF7ED', borderRadius: 12, padding: 14, marginBottom: 8, borderWidth: 1, borderColor: '#FED7AA' },
  alertaHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  alertaTipo: { color: '#C2410C', fontWeight: '700', fontSize: 15, flex: 1 },
  severidadeBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 12 },
  severidadeText: { fontSize: 11, fontWeight: '700', textTransform: 'uppercase' },
  alertaInfo: { color: '#94A3B8', fontSize: 12, marginTop: 6 },
  alertaDesc: { color: '#78716C', marginTop: 4, fontSize: 13 },
  alertaVazio: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 14, backgroundColor: '#F0FDF4', borderRadius: 12 },
  alertaVazioText: { color: '#16A34A', fontSize: 14 },
  btnHistorico: { backgroundColor: '#EA580C', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', borderRadius: 10, marginTop: 12, paddingHorizontal: 20, paddingVertical: 10, gap: 8 },
  btnHistoricoTxt: { color: '#fff', fontWeight: '600', fontSize: 14 },

  actionsContainer: { marginTop: 32, gap: 12 },
  btnAcaoPrimario: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: '#1B9E5A', paddingVertical: 14, borderRadius: 14 },
  btnAcaoPrimarioText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  btnAcaoSecundario: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: '#F0FDF4', paddingVertical: 14, borderRadius: 14, borderWidth: 1, borderColor: '#BBF7D0' },
  btnAcaoSecundarioText: { color: '#1B9E5A', fontWeight: '700', fontSize: 16 },
  // Enriquecimento
  seloBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  seloText: { fontSize: 11, fontWeight: '700' },
  confiancaContainer: { marginTop: 12, marginBottom: 8 },
  confiancaLabel: { fontSize: 12, color: '#64748B', marginBottom: 4 },
  progressBarBg: { height: 8, backgroundColor: '#E2E8F0', borderRadius: 4, overflow: 'hidden' },
  progressBarFill: { height: 8, borderRadius: 4 },
  confiancaValue: { fontSize: 12, color: '#475569', fontWeight: '600', marginTop: 2, textAlign: 'right' },
  occRow: { flexDirection: 'row', gap: 12, marginTop: 12 },
  occCard: { flex: 1, backgroundColor: '#F8FAFC', borderRadius: 12, padding: 12, alignItems: 'center', borderWidth: 1, borderColor: '#E2E8F0' },
  occNumber: { fontSize: 20, fontWeight: '800' },
  occLabel: { fontSize: 11, color: '#94A3B8', marginTop: 2 },
  sinonimoContainer: { marginTop: 12 },
  sinonimoTitle: { fontSize: 13, fontWeight: '700', color: '#475569', marginBottom: 6 },
  sinonimoWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  sinonimoBadge: { backgroundColor: '#F1F5F9', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8, borderWidth: 1, borderColor: '#E2E8F0' },
  sinonimoText: { fontSize: 12, color: '#475569', fontStyle: 'italic' },
  fenologiaContainer: { marginTop: 12 },
  fenologiaPico: { fontSize: 12, color: '#64748B', marginTop: 4 },
  refImageContainer: { marginTop: 12, alignItems: 'center' },
  refImage: { width: '100%', height: 180, borderRadius: 12, resizeMode: 'cover' },
  refImageCaption: { fontSize: 11, color: '#94A3B8', marginTop: 4 },
  refImageLicense: { fontSize: 10, color: '#CBD5E1' },
  lastValidation: { fontSize: 11, color: '#94A3B8', marginTop: 8 },
});
