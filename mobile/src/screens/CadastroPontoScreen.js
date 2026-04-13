import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Image, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import offlineService from '../services/offlineService';
import aiAssistService from '../services/aiAssistService';
import identificacaoService from '../services/identificacaoService';
import { enriquecerNome } from '../services/enriquecimentoService';
import { getFallbackEnrichmentText, normalizeEnrichmentData } from '../utils/enrichmentStatus';

const TIPOS_LOCAL_VALIDOS = [
  { value: 'quintal', label: 'Quintal', icon: 'home-outline' },
  { value: 'reserva', label: 'Reserva', icon: 'leaf-outline' },
  { value: 'rua', label: 'Beira de rua', icon: 'car-outline' },
  { value: 'outro', label: 'Outro', icon: 'ellipsis-horizontal' },
];

const FormSection = ({ title, icon, children }) => (
  <View style={styles.section}>
    <View style={styles.sectionHeader}>
      <Ionicons name={icon} size={18} color="#1B9E5A" />
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
    {children}
  </View>
);

export default function CadastroPontoScreen({ navigation, route }) {
  const insets = useSafeAreaInsets();
  const [form, setForm] = useState({
    nome_popular: '',
    nome_cientifico: '',
    planta_id: null,
    tipo_local: 'outro',
    grupo: '',
    relato: '',
    comestibilidade_status: 'indeterminado',
    parte_comestivel_manual: '',
    frutificacao_manual: '',
    colheita_manual: '',
  });
  const [foto, setFoto] = useState(null);
  const [localizacao, setLocalizacao] = useState(null);
  const [loading, setLoading] = useState(false);
  const [identificandoFoto, setIdentificandoFoto] = useState(false);
  const [statusIdentificacao, setStatusIdentificacao] = useState('');
  const [fonteIdentificacao, setFonteIdentificacao] = useState('');
  const [sugestoesBusca, setSugestoesBusca] = useState([]);
  const [loadingBusca, setLoadingBusca] = useState(false);
  const [plantaInfo, setPlantaInfo] = useState(null);
  const [enrichmentResumo, setEnrichmentResumo] = useState({ status_enriquecimento: 'pendente' });

  useEffect(() => {
    const plantaIdentificada = route?.params?.plantaIdentificada;
    if (!plantaIdentificada) return;

    setForm((prev) => ({
      ...prev,
      nome_popular: plantaIdentificada.nomePopular || prev.nome_popular,
      nome_cientifico: plantaIdentificada.nomeCientifico || prev.nome_cientifico,
      planta_id: plantaIdentificada.plantaId || prev.planta_id,
    }));

    if (plantaIdentificada.fotoUri) {
      setFoto(plantaIdentificada.fotoUri);
    }
  }, [route?.params?.plantaIdentificada]);

  const obterLocalizacao = async () => {
    setLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permissão negada', 'Não foi possível acessar sua localização.');
        return;
      }
      const location = await Location.getCurrentPositionAsync({});
      setLocalizacao([location.coords.longitude, location.coords.latitude]);
    } catch (err) {
      Alert.alert('Erro ao obter localização', err.message);
    } finally {
      setLoading(false);
    }
  };

  const escolherImagem = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({ allowsEditing: true, quality: 0.7, base64: false, mediaTypes: ImagePicker.MediaType?.images ? [ImagePicker.MediaType.images] : ['images'] });
    if (!result.canceled && result.assets?.[0]) {
      const fotoUri = result.assets[0].uri;
      setFoto(fotoUri);
      await identificarFotoNoCadastro(fotoUri);
    }
  };

  const identificarFotoNoCadastro = async (fotoUri) => {
    setIdentificandoFoto(true);
    setStatusIdentificacao('Analisando imagem...');
    try {
      const resultado = await identificacaoService.identificarPlanta(fotoUri, {
        usarCustomDB: true,
        usarGoogle: true,
        salvarHistorico: false,
      });

      if (!resultado?.sucesso) {
        setStatusIdentificacao('Identificação inconclusiva.');
        setFonteIdentificacao('');
        return;
      }

      const dados = resultado.dados || {};
      setForm((prev) => ({
        ...prev,
        nome_popular: dados.nome_popular || prev.nome_popular,
        nome_cientifico: dados.nome_cientifico || prev.nome_cientifico,
        planta_id: dados.planta_base_id || prev.planta_id,
      }));

      if (dados.parte_comestivel || dados.epoca_frutificacao || dados.forma_uso) {
        setPlantaInfo({
          parteComestivel: dados.parte_comestivel || '',
          formaUso: dados.forma_uso || '',
          epocaFrutificacao: dados.epoca_frutificacao || '',
          epocaColheita: dados.epoca_colheita || '',
        });
        setForm((prev) => ({
          ...prev,
          parte_comestivel_manual: prev.parte_comestivel_manual || (dados.parte_comestivel || ''),
          frutificacao_manual: prev.frutificacao_manual || (dados.epoca_frutificacao || ''),
          colheita_manual: prev.colheita_manual || (dados.epoca_colheita || ''),
        }));
      }

      const score = Math.round((dados.score || 0) * 100);
      const origem = dados?.origem_dados === 'cache_integrado_local'
        ? 'Base integrada local (apoio)'
        : (dados?.offline ? 'Base offline' : 'Integrações online');
      setFonteIdentificacao(dados?.fonte_integracao || dados?.metodo || origem);
      setStatusIdentificacao(`Identificação: ${dados.nome_popular || 'concluída'}. Confiança: ${score}%`);
    } catch (error) {
      setStatusIdentificacao('Erro na integração de identificação.');
      setFonteIdentificacao('');
    } finally {
      setIdentificandoFoto(false);
    }
  };

  const identificarComIAOnlineCadastro = async () => {
    if (!foto) {
      Alert.alert('Foto obrigatória', 'Selecione uma imagem para buscar com IA.');
      return;
    }
    await identificarFotoNoCadastro(foto);
  };

  useEffect(() => {
    if (!form.nome_popular || form.nome_popular.length < 2) {
      setSugestoesBusca([]);
      return undefined;
    }

    const timeout = setTimeout(async () => {
      setLoadingBusca(true);
      try {
        const resultado = await identificacaoService.buscarPlantas(form.nome_popular);
        const lista = resultado?.dados?.resultados
          || resultado?.dados?.plantas
          || resultado?.dados?.plantas_referenciais
          || resultado?.dados
          || [];
        setSugestoesBusca(Array.isArray(lista) ? lista.slice(0, 5) : []);
      } finally {
        setLoadingBusca(false);
      }
    }, 400);

    return () => clearTimeout(timeout);
  }, [form.nome_popular]);

  const selecionarSugestao = (item) => {
    setForm((f) => ({
      ...f,
      planta_id: item.id || item.planta_id || f.planta_id,
      nome_popular: item.nome_popular || f.nome_popular,
      nome_cientifico: item.nome_cientifico || f.nome_cientifico,
    }));
    setSugestoesBusca([]);

    if (item.parte_comestivel || item.epoca_frutificacao || item.forma_uso) {
      setPlantaInfo({
        parteComestivel: item.parte_comestivel || '',
        formaUso: item.forma_uso || '',
        epocaFrutificacao: item.epoca_frutificacao || '',
        epocaColheita: item.epoca_colheita || '',
      });
      setForm((prev) => ({
        ...prev,
        parte_comestivel_manual: prev.parte_comestivel_manual || (item.parte_comestivel || ''),
        frutificacao_manual: prev.frutificacao_manual || (item.epoca_frutificacao || ''),
        colheita_manual: prev.colheita_manual || (item.epoca_colheita || ''),
      }));
    }
  };

  const sugerirComIA = async () => {
    if (!form.relato && !foto) {
      Alert.alert('Dados insuficientes', 'Adicione relato ou imagem para gerar sugestão.');
      return;
    }

    const resultado = await aiAssistService.sugerirCadastro({
      observacaoTexto: form.relato,
      localizacao,
      imagemUri: foto,
    });

    if (!resultado.sucesso) {
      Alert.alert('IA offline', resultado.erro);
      return;
    }

    setForm((prev) => ({
      ...prev,
      nome_popular: prev.nome_popular || resultado.preCadastro.nome_popular,
      nome_cientifico: prev.nome_cientifico || resultado.preCadastro.nome_cientifico,
    }));

    Alert.alert('Sugestão aplicada', `Confiança da IA: ${(resultado.inferencia.confianca * 100).toFixed(0)}%`);
  };

  const enviarCadastro = async () => {
    if (!form.nome_popular || !localizacao) {
      Alert.alert('Campos obrigatórios', 'Preencha nome popular e permita a localização.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...form,
        localizacao,
        foto_uri: foto,
        origem: 'mobile',
        colaborador: form.grupo || undefined,
      };

      const resultado = await offlineService.registrarPonto(payload);
      if (!resultado?.sucesso) {
        Alert.alert('Falha no cadastro', resultado?.message || resultado?.erro || 'Não foi possível enviar o ponto.');
        return;
      }

      // Enriquecimento taxonômico em background (não bloqueia)
      if (form.nome_cientifico && resultado.origem !== 'offline') {
        enriquecerNome(form.nome_cientifico, form.planta_id).catch(() => {});
      }

      if (resultado.origem === 'offline') {
        Alert.alert('Salvo offline', 'Registro salvo no dispositivo. O enriquecimento taxonômico será feito na sincronização.');
      } else {
        Alert.alert('Cadastro realizado!', 'Seu ponto foi enviado. O enriquecimento taxonômico está sendo processado automaticamente.');
      }
      navigation.navigate('Home');
    } catch (e) {
      Alert.alert('Erro ao cadastrar', e.message);
    } finally {
      setLoading(false);
    }
  };

  const enrichmentNormalized = normalizeEnrichmentData(enrichmentResumo || {});
  const enrichmentFallbackText = getFallbackEnrichmentText(enrichmentNormalized.status_enriquecimento);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={[styles.container, { paddingBottom: Math.max(24, insets.bottom + 16) }]}>
        {/* Header */}
        <View style={styles.headerRow}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Ionicons name="arrow-back" size={22} color="#1B9E5A" />
          </TouchableOpacity>
          <Text style={styles.titulo}>Novo Ponto de PANC</Text>
        </View>

        {/* Identificação */}
        <FormSection title="Identificação" icon="leaf">
          <TextInput
            style={styles.input}
            placeholder="Nome popular *"
            placeholderTextColor="#94A3B8"
            value={form.nome_popular}
            onChangeText={(v) => setForm((f) => ({ ...f, nome_popular: v }))}
          />
          {loadingBusca && <ActivityIndicator size="small" color="#1B9E5A" style={{ marginBottom: 6 }} />}
          {sugestoesBusca.map((item, idx) => (
            <TouchableOpacity
              key={`${item.id || item.nome_cientifico || item.nome_popular || idx}`}
              style={styles.sugestaoItem}
              onPress={() => selecionarSugestao(item)}
            >
              <Ionicons name="leaf-outline" size={16} color="#1B9E5A" />
              <View style={styles.sugestaoInfo}>
                <Text style={styles.sugestaoTitulo}>{item.nome_popular || 'Sugestão'}</Text>
                {!!item.nome_cientifico && <Text style={styles.sugestaoSub}>{item.nome_cientifico}</Text>}
                {!!item.parte_comestivel && <Text style={styles.sugestaoMeta}>Parte comestível: {item.parte_comestivel}</Text>}
              </View>
            </TouchableOpacity>
          ))}
          <TextInput
            style={styles.input}
            placeholder="Nome científico (opcional)"
            placeholderTextColor="#94A3B8"
            value={form.nome_cientifico}
            onChangeText={(v) => setForm((f) => ({ ...f, nome_cientifico: v }))}
          />
          <View style={styles.enrichmentCard}>
            <Text style={styles.enrichmentText}>
              {form.nome_cientifico
                ? `Nome informado: ${form.nome_cientifico}`
                : 'Informe um nome científico para aumentar a qualidade do enriquecimento.'}
            </Text>
            {!!enrichmentNormalized.nome_cientifico_validado && (
              <Text style={styles.enrichmentText}>Validado: {enrichmentNormalized.nome_cientifico_validado}</Text>
            )}
            {enrichmentNormalized.comestibilidade_confirmada && (
              <Text style={styles.enrichmentText}>Comestível (integração): {enrichmentNormalized.comestibilidade_label}</Text>
            )}
            {enrichmentNormalized.parte_comestivel_confirmada && (
              <Text style={styles.enrichmentText}>Parte comestível: {enrichmentNormalized.parte_comestivel}</Text>
            )}
            {enrichmentNormalized.frutificacao_confirmada && (
              <Text style={styles.enrichmentText}>Frutificação: {enrichmentNormalized.frutificacao_meses}</Text>
            )}
            {enrichmentNormalized.colheita_confirmada && (
              <Text style={styles.enrichmentText}>Colheita: {enrichmentNormalized.colheita_periodo}</Text>
            )}
            {enrichmentNormalized.validacao_pendente_revisao_humana && <Text style={styles.enrichmentWarning}>Revisão humana necessária.</Text>}
            {!!enrichmentFallbackText && <Text style={styles.enrichmentFallback}>{enrichmentFallbackText}</Text>}
          </View>
        </FormSection>

        {/* Info da planta (das integrações) */}
        {plantaInfo && (plantaInfo.parteComestivel || plantaInfo.formaUso || plantaInfo.epocaFrutificacao) && (
          <View style={styles.plantaInfoCard}>
            <View style={styles.plantaInfoHeader}>
              <Ionicons name="information-circle" size={18} color="#1B9E5A" />
              <Text style={styles.plantaInfoTitle}>Informações da planta</Text>
            </View>
            {!!plantaInfo.parteComestivel && (
              <View style={styles.plantaInfoRow}>
                <Ionicons name="checkmark-circle" size={15} color="#16A34A" />
                <Text style={styles.plantaInfoText}>Comestível - Parte: <Text style={styles.bold}>{plantaInfo.parteComestivel}</Text></Text>
              </View>
            )}
            {!!plantaInfo.formaUso && (
              <View style={styles.plantaInfoRow}>
                <Ionicons name="restaurant-outline" size={15} color="#0EA5E9" />
                <Text style={styles.plantaInfoText}>Uso: <Text style={styles.bold}>{plantaInfo.formaUso}</Text></Text>
              </View>
            )}
            {!!plantaInfo.epocaFrutificacao && (
              <View style={styles.plantaInfoRow}>
                <Ionicons name="flower-outline" size={15} color="#D97706" />
                <Text style={styles.plantaInfoText}>Frutificação: <Text style={styles.bold}>{plantaInfo.epocaFrutificacao}</Text></Text>
              </View>
            )}
            {!!plantaInfo.epocaColheita && (
              <View style={styles.plantaInfoRow}>
                <Ionicons name="calendar-outline" size={15} color="#7C3AED" />
                <Text style={styles.plantaInfoText}>Colheita: <Text style={styles.bold}>{plantaInfo.epocaColheita}</Text></Text>
              </View>
            )}
          </View>
        )}

        {/* Tipo de Local */}
        <FormSection title="Uso alimentar e sazonalidade" icon="nutrition">
          <View style={styles.tipoLocalRow}>
            {[
              { value: 'indeterminado', label: 'Não informado' },
              { value: 'sim', label: 'Comestível' },
              { value: 'nao', label: 'Não comestível' },
            ].map((opcao) => (
              <TouchableOpacity
                key={opcao.value}
                style={[styles.tipoLocalChip, form.comestibilidade_status === opcao.value && styles.tipoLocalChipAtivo]}
                onPress={() => setForm((f) => ({ ...f, comestibilidade_status: opcao.value }))}
              >
                <Text style={[styles.tipoLocalChipText, form.comestibilidade_status === opcao.value && styles.tipoLocalChipTextAtivo]}>{opcao.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <TextInput
            style={styles.input}
            placeholder="Parte comestível (ex: folha, fruto)"
            placeholderTextColor="#94A3B8"
            value={form.parte_comestivel_manual}
            onChangeText={(v) => setForm((f) => ({ ...f, parte_comestivel_manual: v }))}
          />
          <TextInput
            style={styles.input}
            placeholder="Frutificação (ex: jan, fev)"
            placeholderTextColor="#94A3B8"
            value={form.frutificacao_manual}
            onChangeText={(v) => setForm((f) => ({ ...f, frutificacao_manual: v }))}
          />
          <TextInput
            style={styles.input}
            placeholder="Colheita (ex: mar a jun)"
            placeholderTextColor="#94A3B8"
            value={form.colheita_manual}
            onChangeText={(v) => setForm((f) => ({ ...f, colheita_manual: v }))}
          />
        </FormSection>

        {/* Tipo de Local */}
        <FormSection title="Local" icon="location">
          <View style={styles.tipoLocalRow}>
            {TIPOS_LOCAL_VALIDOS.map((opcao) => (
              <TouchableOpacity
                key={opcao.value}
                style={[styles.tipoLocalChip, form.tipo_local === opcao.value && styles.tipoLocalChipAtivo]}
                onPress={() => setForm((f) => ({ ...f, tipo_local: opcao.value }))}
              >
                <Ionicons
                  name={opcao.icon}
                  size={16}
                  color={form.tipo_local === opcao.value ? '#fff' : '#64748B'}
                />
                <Text style={[styles.tipoLocalChipText, form.tipo_local === opcao.value && styles.tipoLocalChipTextAtivo]}>{opcao.label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={[styles.locationBtn, localizacao && styles.locationBtnActive]}
            onPress={obterLocalizacao}
          >
            <Ionicons name={localizacao ? 'checkmark-circle' : 'locate'} size={20} color={localizacao ? '#16A34A' : '#1B9E5A'} />
            <Text style={[styles.locationBtnText, localizacao && { color: '#16A34A' }]}>
              {localizacao ? 'Localização capturada!' : 'Obter Localização *'}
            </Text>
          </TouchableOpacity>
        </FormSection>

        {/* Dados Adicionais */}
        <FormSection title="Dados Adicionais" icon="create">
          <TextInput
            style={styles.input}
            placeholder="Grupo / Comunidade"
            placeholderTextColor="#94A3B8"
            value={form.grupo}
            onChangeText={(v) => setForm((f) => ({ ...f, grupo: v }))}
          />
          <TextInput
            style={[styles.input, styles.inputMultiline]}
            placeholder="Relato ou observação sobre a planta"
            placeholderTextColor="#94A3B8"
            value={form.relato}
            onChangeText={(v) => setForm((f) => ({ ...f, relato: v }))}
            multiline
            textAlignVertical="top"
          />
        </FormSection>

        {/* Foto */}
        <FormSection title="Foto" icon="camera">
          <TouchableOpacity style={styles.fotoBtn} onPress={escolherImagem}>
            <Ionicons name="camera-outline" size={22} color="#1B9E5A" />
            <Text style={styles.fotoBtnText}>Selecionar foto</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.identificarIaBtn} onPress={identificarComIAOnlineCadastro}>
            <Ionicons name="sparkles-outline" size={18} color="#fff" />
            <Text style={styles.identificarIaBtnText}>Buscar com IA (integrações)</Text>
          </TouchableOpacity>
          {foto && (
            <View style={styles.fotoPreviewContainer}>
              <Image source={{ uri: foto }} style={styles.fotoPreview} />
              <TouchableOpacity style={styles.fotoRemove} onPress={() => { setFoto(null); setStatusIdentificacao(''); setFonteIdentificacao(''); setPlantaInfo(null); }}>
                <Ionicons name="close-circle" size={24} color="#DC2626" />
              </TouchableOpacity>
            </View>
          )}
          {!!statusIdentificacao && (
            <View style={styles.statusRow}>
              {identificandoFoto ? (
                <ActivityIndicator color="#1B9E5A" size="small" />
              ) : (
                <Ionicons name="information-circle-outline" size={16} color="#0EA5E9" />
              )}
              <Text style={styles.statusText}>{statusIdentificacao}</Text>
            </View>
          )}
          {!!fonteIdentificacao && <Text style={styles.statusFonte}>Fonte: {fonteIdentificacao}</Text>}
        </FormSection>

        {/* IA Assist */}
        <TouchableOpacity style={styles.iaBtn} onPress={sugerirComIA}>
          <Ionicons name="sparkles" size={18} color="#fff" />
          <Text style={styles.iaBtnText}>Sugerir com IA offline</Text>
        </TouchableOpacity>

        {/* Nota enriquecimento */}
        <View style={styles.enrichmentNote}>
          <Ionicons name="information-circle-outline" size={16} color="#0EA5E9" />
          <Text style={styles.enrichmentNoteText}>
            Ao cadastrar, o sistema validará automaticamente os dados via Global Names, Tropicos, GBIF e iNaturalist.
          </Text>
        </View>

        {/* Submit */}
        <TouchableOpacity
          style={[styles.submitBtn, loading && { opacity: 0.6 }]}
          onPress={enviarCadastro}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <>
              <Ionicons name="cloud-upload" size={20} color="#fff" />
              <Text style={styles.submitBtnText}>Cadastrar Ponto</Text>
            </>
          )}
        </TouchableOpacity>

        <Text style={styles.obs}>* Campos obrigatórios</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#F8FAFC' },
  container: { padding: 16 },

  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  backBtn: { width: 40, height: 40, borderRadius: 12, backgroundColor: '#F0FDF4', justifyContent: 'center', alignItems: 'center' },
  titulo: { fontWeight: '800', fontSize: 22, color: '#0F172A' },

  section: { marginBottom: 20 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: '#1B9E5A' },

  input: {
    backgroundColor: '#fff',
    borderRadius: 12,
    borderColor: '#E2E8F0',
    borderWidth: 1,
    fontSize: 15,
    padding: 14,
    marginBottom: 10,
    color: '#0F172A',
  },
  inputMultiline: { height: 80, textAlignVertical: 'top' },

  sugestaoItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#fff',
    borderColor: '#E2E8F0',
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginBottom: 6,
  },
  sugestaoInfo: { flex: 1 },
  sugestaoTitulo: { color: '#0F172A', fontWeight: '700', fontSize: 14 },
  sugestaoSub: { color: '#94A3B8', fontSize: 12, fontStyle: 'italic', marginTop: 2 },
  sugestaoMeta: { color: '#16A34A', fontSize: 11, marginTop: 2 },
  enrichmentCard: { backgroundColor: '#F8FAFC', borderRadius: 12, borderWidth: 1, borderColor: '#E2E8F0', padding: 12, marginTop: 4 },
  enrichmentText: { color: '#475569', fontSize: 12, marginTop: 2 },
  enrichmentFallback: { color: '#92400E', fontSize: 12, marginTop: 4 },
  enrichmentWarning: { color: '#B45309', fontSize: 12, marginTop: 4, fontWeight: '700' },

  plantaInfoCard: {
    backgroundColor: '#F0FDF4',
    borderRadius: 14,
    padding: 14,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    gap: 8,
  },
  plantaInfoHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 },
  plantaInfoTitle: { fontSize: 14, fontWeight: '700', color: '#1B9E5A' },
  plantaInfoRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  plantaInfoText: { color: '#475569', fontSize: 13, flex: 1 },
  bold: { fontWeight: '700', color: '#0F172A' },

  tipoLocalRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  tipoLocalChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: '#fff',
  },
  tipoLocalChipAtivo: { backgroundColor: '#1B9E5A', borderColor: '#1B9E5A' },
  tipoLocalChipText: { color: '#64748B', fontSize: 13, fontWeight: '600' },
  tipoLocalChipTextAtivo: { color: '#fff' },

  locationBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 14,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderStyle: 'dashed',
  },
  locationBtnActive: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0', borderStyle: 'solid' },
  locationBtnText: { color: '#1B9E5A', fontWeight: '600', fontSize: 14 },

  fotoBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 14,
    backgroundColor: '#fff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderStyle: 'dashed',
  },
  fotoBtnText: { color: '#1B9E5A', fontWeight: '600', fontSize: 14 },
  identificarIaBtn: {
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#1B9E5A',
    borderRadius: 12,
    paddingVertical: 12,
  },
  identificarIaBtnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  fotoPreviewContainer: { position: 'relative', marginTop: 10 },
  fotoPreview: { width: '100%', height: 200, borderRadius: 14, backgroundColor: '#E2E8F0' },
  fotoRemove: { position: 'absolute', top: 8, right: 8, backgroundColor: '#fff', borderRadius: 12 },

  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8 },
  statusText: { color: '#475569', fontSize: 13, flex: 1 },
  statusFonte: { color: '#0F766E', fontSize: 12, marginTop: 6, fontWeight: '600' },

  iaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#6366F1',
    padding: 14,
    borderRadius: 14,
    marginBottom: 12,
  },
  iaBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },

  submitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#1B9E5A',
    padding: 16,
    borderRadius: 14,
    marginBottom: 8,
  },
  submitBtnText: { color: '#fff', fontWeight: '800', fontSize: 16 },
  enrichmentNote: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, backgroundColor: '#EFF6FF', borderRadius: 12, padding: 12, marginBottom: 12 },
  enrichmentNoteText: { flex: 1, fontSize: 12, color: '#475569', lineHeight: 18 },

  obs: { color: '#94A3B8', fontSize: 12, textAlign: 'center', marginTop: 4 },
});
