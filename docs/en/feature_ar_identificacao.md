# AR Functionalities and Advanced Plant Identification

## Overview

This document describes the new features implemented in the ColaboraPANC project:

1. **Augmented Reality (AR)** - Viewing plants in 3D
2. **Advanced Plant Identification** - Multi-source system with Google Vision, PlantNet and customized base

---

## 🌟 Implemented Features

### 1. Multi-Source Identification System

The system now identifies plants using multiple sources with automatic fallback:

**Attempt Order:**
1. **Customized Database** (local) - Specific plants that do not standardize
2. **Google Cloud Vision API** - Powerful visual identification
3. **PlantNet API** - Specialized in plants
4. **Plant.id API** - Final Fallback

#### Features:
- ✅ Fast identification (< 5 seconds on average)
- ✅ Complete identification history
- ✅ Confidence score for each result
- ✅ Support for customized plans validated by experts

---

### 2. Custom Plant Database

Allows you to register specific plant variations that are not correctly identified by public APIs.

#### Django Models Created:

**Customized Plant**
- Variation name
- Reference photos (leaf, flower, fruit, whole plant)
- Visual characteristics (color, shape, texture)
- ML features for automatic comparison
- Validation by experts

**ModelAR**
- 3D models in GLB/GLTF/USDZ format
- Scale and positioning settings
- Animation support
- Image preview

**HistoryIdentification**
- Record of all attempts
- Method used
- Confidence score
- Processing time
- Usage statistics

---

### 3. Augmented Reality

Viewing plants in 3D using the device's camera.

#### Features:
- 📱 GLB/GLTF model support
- 🔄 Interactive models (rotation, scale)
- 📦 Download on demand
- 🎨 Preview before loading

---

## 📡 API Endpoints

### Identification

```
POST /api/identificar-planta/
```
**Body (multipart/form-data):**
- `imagem`: image file
- `usar_custom_db`: boolean (default: true)
- `usar_google`: boolean (default: true)
- `salvar_historico`: boolean (default: true)
- `ponto_id`: int (optional)

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

### Search Plants

```
GET /api/buscar-plantas/?q=termo
```

### AR Models

```
GET /api/modelos-ar-disponiveis/?planta=<id>
GET /api/modelos-ar/
POST /api/modelos-ar/
```

### Customized Plants

```
GET /api/plantas-customizadas/
POST /api/plantas-customizadas/
POST /api/plantas-customizadas/<id>/validar/
POST /api/plantas-customizadas/<id>/extrair_features/
```

### History

```
GET /api/historico-identificacao/
GET /api/historico-identificacao/estatisticas/
```

---

## 📱 Use on Mobile

### Identification Service

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

### Created Screens

**IdentifyPlantaScreen.js**
- Camera with framing
- Photo or gallery capture
- Automatic identification
- Display of results
- Integration with points registration

**PlantaARScreen.js**
- AR visualization of plants
- Selection of 3D models
- Interaction controls
- Model information

---

## ⚙️ Configuration

### Backend (Django)

1. **Install dependencies:**
```bash
pip install google-cloud-vision scikit-learn scipy numpy Pillow
```

2. **Set up Google Cloud Vision:**

Create a Google Cloud account and obtain credentials:

```bash
# Criar arquivo de credenciais
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

Or configure it in `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
PLANTNET_API_KEY=sua_chave_aqui
PLANTID_API_KEY=sua_chave_aqui
```

3. **Run migrations:**
```bash
python manage.py makemigrations mapping
python manage.py migrate
```

4. **Create group of experts (optional):**
```python
python manage.py shell

from django.contrib.auth.models import Group
Group.objects.create(name='Especialistas')
```

### Mobile (React Native)

1. **Install dependencies:**
```bash
npm install expo-camera expo-gl expo-file-system
# ou
yarn add expo-camera expo-gl expo-file-system
```

2. **Configure permissions in app.json:**
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

3. **Add navigation routes:**
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

## 🚀 How to Use

### For Users

1. **Identify a Plant:**
- Open the app
- Tap "Identify Plant"
- Take a photo or choose from the gallery
- Wait for identification
- See results with confidence score

2. **View in AR:**
- After identifying a plant
- Tap "View in AR"
- Point the camera at a surface
- See the 3D model of the plant

3. **Register Customized Plant:**
- If identification fails repeatedly
- Register a specific variation
- Add reference photos
- Wait for expert validation

### For Experts

1. **Validate Custom Plants:**
```python
# Via admin Django ou API
POST /api/plantas-customizadas/<id>/validar/
```

2. **Add AR Models:**
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

## 📊 Statistics and Monitoring

### View Personal Statistics

```javascript
const stats = await identificacaoService.obterEstatisticasIdentificacao();

console.log(stats.estatisticas.total_identificacoes);
console.log(stats.estatisticas.taxa_sucesso);
console.log(stats.estatisticas.por_metodo);
```

### Admin Django

Go to `/admin/` to:
- View all IDs
- Approve customized plans
- Upload AR models
- General statistics

---

## 🔧 Troubleshooting

### Google Cloud Vision does not work

**Problem:** "Could not authenticate" error

**Solution:**
1. Check if the credentials file exists
2. Confirm the `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Check if the API is enabled in the Google Cloud Console

### PlantNet/Plant.id returns error 429

**Problem:** Request limit exceeded

**Solution:**
- APIs have monthly limits (PlantNet: 1000, Plant.id: 50)
- The system uses automatic fallback
- Consider using the custom base more

### AR models do not load

**Problem:** File too large or invalid format

**Solution:**
1. Make sure you use GLB/GLTF
2. Optimize the template (< 10MB recommended)
3. Use tools like gltf-pipeline for compression

---

## 🎯 Next Steps

- [ ] Implement AR model caching
- [ ] Add offline support for identification
- [ ] Train your own ML model with local dataset
- [ ] Integration with native ARCore/ARKit
- [ ] AR multiplayer mode (view plants together)
- [ ] Export of custom 3D models

---

## 📚 References

- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [PlantNet API](https://my.plantnet.org/)
- [Plant.id API](https://plant.id/)
- [Expo Camera](https://docs.expo.dev/versions/latest/sdk/camera/)
- [Expo GL](https://docs.expo.dev/versions/latest/sdk/gl-view/)
- [Three.js](https://threejs.org/) (for 3D rendering)

---

## 👥 Contributing

To add new identification sources:

1. Edit `mapping/identificacao_avancada.py`
2. Add new `_identificar_<fonte>` method
3. Add to fallback flow in `identificar()`
4. Update documentation

To add support for new AR formats:

1. Edit `mapping/models.py` → ARModel
2. Add format to choices
3. Update renderer on mobile

---

## 📄 License

This code is part of the ColaboraPANC project.
