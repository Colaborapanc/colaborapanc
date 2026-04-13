# Selective Offline Plant System

## 📋 Overview

The Selective Offline Plants system allows users to choose specific plants for download and offline use, generating a minimum viable database for identification without an internet connection.

### Benefits

- ✅ **Space Saving**: Download only the plans you need
- ✅ **Offline Identification**: Identify plants even without internet
- ✅ **Theme Packs**: Download sets of plants by biome or region
- ✅ **Smart Management**: Storage control and automatic cleaning
- ✅ **Synchronization**: Keep plans updated automatically

---

## 🏗️ System Architecture

### Backend (Django)

#### Models

**PlantOfflineUser**
- Tracks blueprints downloaded by each user
- Stores complete plant data in JSON
- Controls download status (pending, downloading, completed, error)
- Records usage statistics

**OfflinePlantsPackage**
- Groups plants into themed packages
- Facilitates batch download
- Filterable by biome, region, difficulty

**Offline Configuration**
- User download preferences
- Storage limits
- Auto-update settings

#### API endpoints

```
GET  /api/plantas-offline/disponiveis/          # Lista plantas disponíveis
GET  /api/plantas-offline/pacotes/              # Lista pacotes pré-definidos
POST /api/plantas-offline/baixar/               # Inicia download de plantas
GET  /api/plantas-offline/<id>/dados/           # Obtém dados completos de uma planta
GET  /api/plantas-offline/minhas/               # Lista plantas baixadas
DELETE /api/plantas-offline/<id>/remover/       # Remove planta offline
GET/PUT /api/plantas-offline/configuracoes/     # Gerencia configurações
POST /api/plantas-offline/sincronizar/          # Sincroniza status
POST /api/plantas-offline/pacotes/<id>/baixar/  # Baixa pacote completo
```

### Mobile (React Native)

#### Services

**plantsOfflineService.js**
- Manages download and local storage
- Implements offline identification
- Synchronizes with the server
- Calculates similarity between images

**identificacaoService.js** (Adapted)
- Try offline identification first
- Fallback for online identification
- Automatic connectivity detection

#### Screens

1. **PlantasOfflineScreen**: Search and select plants
2. **MyPlantsOfflineScreen**: Management of downloaded plans
3. **OfflineScreen Settings**: Storage settings and management

---

## 🚀 How to Use

### For Users

#### 1. Download Blueprints

```javascript
// Navegue para PlantasOfflineScreen
navigation.navigate('PlantasOffline');

// Selecione plantas individuais ou escolha um pacote
// Toque em "Baixar" para iniciar o download
```

#### 2. Configure Preferences

```javascript
// Acesse ConfiguracoesOfflineScreen
navigation.navigate('ConfiguracoesOffline');

// Ajuste:
// - Baixar apenas com WiFi
// - Qualidade das fotos (baixa, média, alta)
// - Incluir modelos AR
// - Limite de armazenamento
// - Frequência de atualização
```

#### 3. Identify Offline

```javascript
// Use a função de identificação normalmente
import identificacaoService from './services/identificacaoService';

const resultado = await identificacaoService.identificarPlanta(imageUri, {
  tentarOfflinePrimeiro: true,  // Tenta offline primeiro
  forcarOnline: false,           // Permite fallback para offline
});

if (resultado.sucesso) {
  console.log('Planta:', resultado.dados.nome_popular);
  console.log('Offline:', resultado.dados.offline); // true se identificou offline
}
```

#### 4. Manage Downloaded Blueprints

```javascript
// Navegue para MinhasPlantasOfflineScreen
navigation.navigate('MinhasPlantas');

// Visualize, ordene e remova plantas
// Veja estatísticas de uso de cada planta
```

### For Developers

#### Add New Plant to Catalog

```python
# No Django admin ou shell
from mapping.models import PlantaReferencial

planta = PlantaReferencial.objects.create(
    nome_popular="Ora-pro-nóbis",
    nome_cientifico="Pereskia aculeata",
    parte_comestivel="Folhas",
    forma_uso="Refogado, saladas, sucos",
    grupo_taxonomico="Cactaceae",
    bioma="Mata Atlântica",
    regiao_ocorrencia="Sul, Sudeste",
)
```

#### Create Plant Pack

```python
from mapping.models import PacotePlantasOffline, PlantaReferencial

pacote = PacotePlantasOffline.objects.create(
    nome="PANCs do Cerrado",
    descricao="Plantas alimentícias do bioma Cerrado",
    bioma="Cerrado",
    regiao="Centro-Oeste",
    dificuldade="intermediario",
    tamanho_estimado=50,  # MB
)

# Adicionar plantas ao pacote
plantas_cerrado = PlantaReferencial.objects.filter(bioma="Cerrado")
pacote.plantas.set(plantas_cerrado)
```

#### Implement Feature Extraction

```javascript
// Melhorar a função extrairFeaturesImagem em identificacaoService.js
// Usar bibliotecas como:
// - react-native-image-processing
// - TensorFlow.js
// - react-native-opencv

import { ImageManipulator } from 'expo-image-manipulator';
import * as tf from '@tensorflow/tfjs';

const extrairFeaturesImagem = async (imageUri) => {
  // 1. Redimensionar imagem
  const resized = await ImageManipulator.manipulateAsync(
    imageUri,
    [{ resize: { width: 224, height: 224 } }]
  );

  // 2. Extrair features com ML
  // Implementar modelo de features
  // Retornar histogramas, texturas, etc.

  return features;
};
```

---

## 🔧 Configuration

### Requirements

####Backend
- Django 4.x
- Django REST Framework
- PostgreSQL with PostGIS

#### Mobile
- React Native/Expo
- AsyncStorage
- NetInfo
- Slider component

### Installation

#### 1. Backend

```bash
# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Criar superusuário (se necessário)
python manage.py createsuperuser
```

#### 2. Mobile

```bash
# Instalar dependências
npm install @react-native-async-storage/async-storage
npm install @react-native-community/netinfo
npm install @react-native-community/slider
npm install axios
```

#### 3. Configure URLs

Add to your main routes file:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('', include('mapping.urls')),
]
```

---

## 📊 Data Structure

### Offline Plant Data (JSON)

```json
{
  "id": 1,
  "nome_popular": "Ora-pro-nóbis",
  "nome_cientifico": "Pereskia aculeata",
  "nome_cientifico_valido": "Pereskia aculeata Mill.",
  "parte_comestivel": "Folhas",
  "forma_uso": "Refogado, em omeletes, saladas...",
  "grupo_taxonomico": "Cactaceae",
  "origem": "América do Sul",
  "bioma": "Mata Atlântica",
  "regiao_ocorrencia": "Sul, Sudeste",
  "variacoes": [
    {
      "id": 1,
      "nome_variacao": "Ora-pro-nóbis de folha roxa",
      "descricao": "Variedade com folhas roxas",
      "features_ml": {
        "hist_r": [0.1, 0.2, ...],
        "hist_g": [0.1, 0.2, ...],
        "hist_b": [0.1, 0.2, ...],
        "cor_media": 125.5,
        "textura_std": 45.2
      },
      "fotos": {
        "folha": "https://...",
        "flor": "https://...",
        "fruto": null,
        "planta_inteira": "https://..."
      }
    }
  ],
  "modelos_ar": [],
  "tamanho_total_mb": 0.8,
  "versao": "20260123120000"
}
```

---

## 🎯 Usage Flow

### Scenario 1: New User

1. User accesses offline plant screen
2. See suggested packages (e.g. "PANCs Beginners")
3. Select package and confirm download
4. Blueprints are downloaded in the background
5. User can start identifying offline

### Scenario 2: Experienced User

1. User searches for specific plants by name/biome
2. Select multiple plants
3. Sets (high) quality and includes AR templates
4. Only download what you need
5. Manage storage by removing old plants

### Scenario 3: No Connection

1. User takes a photo of a plant
2. System detects lack of connection
3. Try to identify using an offline basis
4. If a match is found, it shows results
5. If you can't find it, suggest downloading more plans

---

## 🔍 Offline Identification Algorithm

### 1. Feature Extraction

```javascript
const features = {
  // Histogramas de cor (RGB)
  hist_r: [32 bins],
  hist_g: [32 bins],
  hist_b: [32 bins],

  // Estatísticas de cor
  cor_media: float,

  // Textura
  textura_std: float,
};
```

### 2. Comparison

For each downloaded plan:
- Compares histograms using chi-square distance
- Compares average color
- Compare texture
- Calculates normalized average score (0-1)

### 3. Ranking

- Sort plants by score
- Returns the best match if score > 0.6
- Returns top 3 alternatives

---

## 📈 Future Optimizations

### Short Term
- [ ] Implement real feature extraction (TensorFlow.js)
- [ ] Add plant image cache
- [ ] Implement incremental synchronization
- [ ] Add data compression

### Medium Term
- [ ] Train customized ML model for PANCs
- [ ] Implement visual similarity search
- [ ] Add recognition of specific parts (leaf, flower, fruit)
- [ ] Support identification by multiple photos

### Long Term
- [ ] On-device AI model (CoreML/TFLite)
- [ ] Real-time identification with camera
- [ ] Sharing packages between users
- [ ] Collaborative dataset improvement mode

---

## 🐛 Troubleshooting

### Problem: Plants do not lower

**Solution:**
1. Check internet connection
2. Confirm that "Download on WiFi only" is turned off (if using mobile data)
3. Check available space on the device
4. Try clearing cache and downloading again

### Problem: Offline identification does not work

**Solution:**
1. Check for downloaded blueprints
2. Confirm that the plant data is complete
3. Try downloading the plan again
4. Check logs for processing errors

### Problem: Excessive storage usage

**Solution:**
1. Access Offline Settings
2. Reduce photo quality to "medium" or "low"
3. Disable "Include AR Models"
4. Activate "Clear Old Plants"
5. Remove unused plants

---

## 📝 Technical Notes

### Local Storage

- Uses AsyncStorage for metadata
- Each plant has a unique key: `@planta_offline_{id}`
- List of plants: `@plantas_offline_baixadas`
- Settings: `@config_offline`

### Synchronization

- Status sent to the server periodically
- Server keeps record of plants per user
- Allows usage analysis and recommendations

### Security

- Authentication token in all requests
- Data validated in the backend
- Rate limiting to prevent abuse

---

## 👥 Contributing

To contribute to the offline plant system:

1. Fork the repository
2. Create a branch for your feature
3. Implement and test
4. Send a Pull Request

### Areas of Contribution

- Improvements in the identification algorithm
- New plant packs
- User Interface
- Documentation
- Tests

---

## 📄 License

This project is part of the Colabora PANC system.
See the project's main LICENSE file for more information.

---

## 📞 Support

For questions or problems:

1. Open an issue on GitHub
2. Consult the complete documentation
3. Contact the development team

---

**Developed with ❤️ to promote knowledge about PANCs (Non-Conventional Food Plants)**
