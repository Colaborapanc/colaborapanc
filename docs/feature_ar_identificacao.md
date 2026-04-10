# Funcionalidades de AR e Identificação Avançada de Plantas

## Visão Geral

Este documento descreve as novas funcionalidades implementadas no projeto ColaboraPANC:

1. **Realidade Aumentada (AR)** - Visualização de plantas em 3D
2. **Identificação Avançada de Plantas** - Sistema multi-fonte com Google Vision, PlantNet e base customizada

---

## 🌟 Funcionalidades Implementadas

### 1. Sistema de Identificação Multi-Fonte

O sistema agora identifica plantas usando múltiplas fontes com fallback automático:

**Ordem de Tentativa:**
1. **Base de Dados Customizada** (local) - Plantas específicas que fogem ao padrão
2. **Google Cloud Vision API** - Identificação visual poderosa
3. **PlantNet API** - Especializada em plantas
4. **Plant.id API** - Fallback final

#### Características:
- ✅ Identificação rápida (< 5 segundos em média)
- ✅ Histórico completo de identificações
- ✅ Score de confiança para cada resultado
- ✅ Suporte a plantas customizadas validadas por especialistas

---

### 2. Base de Dados Customizada de Plantas

Permite cadastrar variações específicas de plantas que não são identificadas corretamente pelas APIs públicas.

#### Modelos Django Criados:

**PlantaCustomizada**
- Nome da variação
- Fotos de referência (folha, flor, fruto, planta inteira)
- Características visuais (cor, formato, textura)
- Features ML para comparação automática
- Validação por especialistas

**ModeloAR**
- Modelos 3D em formato GLB/GLTF/USDZ
- Configurações de escala e posicionamento
- Suporte a animações
- Preview de imagem

**HistoricoIdentificacao**
- Registro de todas as tentativas
- Método utilizado
- Score de confiança
- Tempo de processamento
- Estatísticas de uso

---

### 3. Realidade Aumentada

Visualização de plantas em 3D usando a câmera do dispositivo.

#### Recursos:
- 📱 Suporte a modelos GLB/GLTF
- 🔄 Modelos interativos (rotação, escala)
- 📦 Download sob demanda
- 🎨 Preview antes de carregar

---

## 📡 Endpoints da API

### Identificação

```
POST /api/identificar-planta/
```
**Body (multipart/form-data):**
- `imagem`: arquivo de imagem
- `usar_custom_db`: boolean (default: true)
- `usar_google`: boolean (default: true)
- `salvar_historico`: boolean (default: true)
- `ponto_id`: int (opcional)

**Response:**
```json
{
  "sucesso": true,
  "metodo": "google_vision",
  "nome_popular": "Ora-pro-nóbis",
  "nome_cientifico": "Pereskia aculeata",
  "score": 0.89,
  "tempo_processamento": 2.3,
  "planta_base_id": 123
}
```

### Buscar Plantas

```
GET /api/buscar-plantas/?q=termo
```

### Modelos AR

```
GET /api/modelos-ar-disponiveis/?planta=<id>
GET /api/modelos-ar/
POST /api/modelos-ar/
```

### Plantas Customizadas

```
GET /api/plantas-customizadas/
POST /api/plantas-customizadas/
POST /api/plantas-customizadas/<id>/validar/
POST /api/plantas-customizadas/<id>/extrair_features/
```

### Histórico

```
GET /api/historico-identificacao/
GET /api/historico-identificacao/estatisticas/
```

---

## 📱 Uso no Mobile

### Serviço de Identificação

```javascript
import identificacaoService from '../services/identificacaoService';

// Identificar planta
const resultado = await identificacaoService.identificarPlanta(
  imageUri,
  {
    usarCustomDB: true,
    usarGoogle: true,
    salvarHistorico: true,
    pontoId: 123
  }
);

// Verificar se resultado é confiável
if (identificacaoService.isResultadoConfiavel(resultado)) {
  const formatado = identificacaoService.formatarResultadoIdentificacao(resultado);
  console.log(formatado.nomePopular);
  console.log(formatado.confianca); // 0-100
}
```

### Telas Criadas

**IdentificarPlantaScreen.js**
- Câmera com enquadramento
- Captura de foto ou galeria
- Identificação automática
- Exibição de resultados
- Integração com cadastro de pontos

**PlantaARScreen.js**
- Visualização AR de plantas
- Seleção de modelos 3D
- Controles de interação
- Informações do modelo

---

## ⚙️ Configuração

### Backend (Django)

1. **Instalar dependências:**
```bash
pip install google-cloud-vision scikit-learn scipy numpy Pillow
```

2. **Configurar Google Cloud Vision:**

Crie uma conta no Google Cloud e obtenha as credenciais:

```bash
# Criar arquivo de credenciais
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

Ou configure no `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
PLANTNET_API_KEY=sua_chave_aqui
PLANTID_API_KEY=sua_chave_aqui
```

3. **Executar migrações:**
```bash
python manage.py makemigrations mapping
python manage.py migrate
```

4. **Criar grupo de especialistas (opcional):**
```python
python manage.py shell

from django.contrib.auth.models import Group
Group.objects.create(name='Especialistas')
```

### Mobile (React Native)

1. **Instalar dependências:**
```bash
npm install expo-camera expo-gl expo-file-system
# ou
yarn add expo-camera expo-gl expo-file-system
```

2. **Configurar permissões no app.json:**
```json
{
  "expo": {
    "plugins": [
      [
        "expo-camera",
        {
          "cameraPermission": "Permite tirar fotos para identificar plantas"
        }
      ]
    ]
  }
}
```

3. **Adicionar rotas de navegação:**
```javascript
// No seu navigator
import IdentificarPlantaScreen from './src/screens/IdentificarPlantaScreen';
import PlantaARScreen from './src/screens/PlantaARScreen';

// Adicionar rotas
<Stack.Screen
  name="IdentificarPlanta"
  component={IdentificarPlantaScreen}
  options={{ title: 'Identificar Planta' }}
/>
<Stack.Screen
  name="PlantaAR"
  component={PlantaARScreen}
  options={{ title: 'Visualizar em AR' }}
/>
```

---

## 🚀 Como Usar

### Para Usuários

1. **Identificar uma Planta:**
   - Abra o app
   - Toque em "Identificar Planta"
   - Tire uma foto ou escolha da galeria
   - Aguarde a identificação
   - Veja os resultados com score de confiança

2. **Visualizar em AR:**
   - Após identificar uma planta
   - Toque em "Ver em AR"
   - Aponte a câmera para uma superfície
   - Veja o modelo 3D da planta

3. **Cadastrar Planta Customizada:**
   - Se a identificação falhar repetidamente
   - Cadastre uma variação específica
   - Adicione fotos de referência
   - Aguarde validação de especialista

### Para Especialistas

1. **Validar Plantas Customizadas:**
```python
# Via admin Django ou API
POST /api/plantas-customizadas/<id>/validar/
```

2. **Adicionar Modelos AR:**
```python
# Upload de modelo 3D
POST /api/modelos-ar/
# Body:
# - planta_id
# - nome
# - modelo_glb (arquivo GLB/GLTF)
# - escala_padrao
```

---

## 📊 Estatísticas e Monitoramento

### Visualizar Estatísticas Pessoais

```javascript
const stats = await identificacaoService.obterEstatisticasIdentificacao();

console.log(stats.estatisticas.total_identificacoes);
console.log(stats.estatisticas.taxa_sucesso);
console.log(stats.estatisticas.por_metodo);
```

### Admin Django

Acesse `/admin/` para:
- Ver todas as identificações
- Aprovar plantas customizadas
- Upload de modelos AR
- Estatísticas gerais

---

## 🔧 Troubleshooting

### Google Cloud Vision não funciona

**Problema:** Erro "Could not authenticate"

**Solução:**
1. Verifique se o arquivo de credenciais existe
2. Confirme a variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS`
3. Verifique se a API está habilitada no Google Cloud Console

### PlantNet/Plant.id retorna erro 429

**Problema:** Limite de requisições excedido

**Solução:**
- As APIs têm limites mensais (PlantNet: 1000, Plant.id: 50)
- O sistema usa fallback automático
- Considere usar mais a base customizada

### Modelos AR não carregam

**Problema:** Arquivo muito grande ou formato inválido

**Solução:**
1. Certifique-se de usar GLB/GLTF
2. Otimize o modelo (< 10MB recomendado)
3. Use ferramentas como gltf-pipeline para compressão

---

## 🎯 Próximos Passos

- [ ] Implementar cache de modelos AR
- [ ] Adicionar suporte offline para identificação
- [ ] Treinar modelo ML próprio com dataset local
- [ ] Integração com ARCore/ARKit nativo
- [ ] Modo multiplayer AR (ver plantas juntos)
- [ ] Exportação de modelos 3D personalizados

---

## 📚 Referências

- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [PlantNet API](https://my.plantnet.org/)
- [Plant.id API](https://plant.id/)
- [Expo Camera](https://docs.expo.dev/versions/latest/sdk/camera/)
- [Expo GL](https://docs.expo.dev/versions/latest/sdk/gl-view/)
- [Three.js](https://threejs.org/) (para renderização 3D)

---

## 👥 Contribuindo

Para adicionar novas fontes de identificação:

1. Edite `mapping/identificacao_avancada.py`
2. Adicione novo método `_identificar_<fonte>`
3. Adicione ao fluxo de fallback em `identificar()`
4. Atualize documentação

Para adicionar suporte a novos formatos AR:

1. Edite `mapping/models.py` → ModeloAR
2. Adicione formato nas choices
3. Atualize renderer no mobile

---

## 📄 Licença

Este código faz parte do projeto ColaboraPANC.
