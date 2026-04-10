# Sistema de Plantas Offline Seletivas

## 📋 Visão Geral

O sistema de Plantas Offline Seletivas permite que os usuários escolham plantas específicas para download e uso offline, gerando uma base de dados mínima viável para identificação sem conexão com a internet.

### Benefícios

- ✅ **Economia de Espaço**: Baixe apenas as plantas que você precisa
- ✅ **Identificação Offline**: Identifique plantas mesmo sem internet
- ✅ **Pacotes Temáticos**: Baixe conjuntos de plantas por bioma ou região
- ✅ **Gestão Inteligente**: Controle de armazenamento e limpeza automática
- ✅ **Sincronização**: Mantenha as plantas atualizadas automaticamente

---

## 🏗️ Arquitetura do Sistema

### Backend (Django)

#### Modelos

**PlantaOfflineUsuario**
- Rastreia plantas baixadas por cada usuário
- Armazena dados completos da planta em JSON
- Controla status de download (pendente, baixando, concluído, erro)
- Registra estatísticas de uso

**PacotePlantasOffline**
- Agrupa plantas em pacotes temáticos
- Facilita download em lote
- Filtrável por bioma, região, dificuldade

**ConfiguracaoOffline**
- Preferências de download do usuário
- Limites de armazenamento
- Configurações de atualização automática

#### Endpoints da API

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

#### Serviços

**plantasOfflineService.js**
- Gerencia download e armazenamento local
- Implementa identificação offline
- Sincroniza com o servidor
- Calcula similaridade entre imagens

**identificacaoService.js** (Adaptado)
- Tenta identificação offline primeiro
- Fallback para identificação online
- Detecção automática de conectividade

#### Telas

1. **PlantasOfflineScreen**: Busca e seleção de plantas
2. **MinhasPlantasOfflineScreen**: Gerenciamento de plantas baixadas
3. **ConfiguracoesOfflineScreen**: Configurações e gestão de armazenamento

---

## 🚀 Como Usar

### Para Usuários

#### 1. Baixar Plantas

```javascript
// Navegue para PlantasOfflineScreen
navigation.navigate('PlantasOffline');

// Selecione plantas individuais ou escolha um pacote
// Toque em "Baixar" para iniciar o download
```

#### 2. Configurar Preferências

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

#### 3. Identificar Offline

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

#### 4. Gerenciar Plantas Baixadas

```javascript
// Navegue para MinhasPlantasOfflineScreen
navigation.navigate('MinhasPlantas');

// Visualize, ordene e remova plantas
// Veja estatísticas de uso de cada planta
```

### Para Desenvolvedores

#### Adicionar Nova Planta ao Catálogo

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

#### Criar Pacote de Plantas

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

#### Implementar Extração de Features

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

## 🔧 Configuração

### Requisitos

#### Backend
- Django 4.x
- Django REST Framework
- PostgreSQL com PostGIS

#### Mobile
- React Native / Expo
- AsyncStorage
- NetInfo
- Slider component

### Instalação

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

#### 3. Configurar URLs

Adicione no seu arquivo de rotas principal:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('', include('mapping.urls')),
]
```

---

## 📊 Estrutura de Dados

### Dados de Planta Offline (JSON)

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

## 🎯 Fluxo de Uso

### Cenário 1: Usuário Novo

1. Usuário acessa tela de plantas offline
2. Vê pacotes sugeridos (ex: "PANCs Iniciantes")
3. Seleciona pacote e confirma download
4. Plantas são baixadas em segundo plano
5. Usuário pode começar a identificar offline

### Cenário 2: Usuário Experiente

1. Usuário busca plantas específicas por nome/bioma
2. Seleciona múltiplas plantas
3. Configura qualidade (alta) e inclui modelos AR
4. Baixa apenas o que precisa
5. Gerencia armazenamento removendo plantas antigas

### Cenário 3: Sem Conexão

1. Usuário tira foto de uma planta
2. Sistema detecta falta de conexão
3. Tenta identificar usando base offline
4. Se encontra correspondência, mostra resultado
5. Se não encontra, sugere baixar mais plantas

---

## 🔍 Algoritmo de Identificação Offline

### 1. Extração de Features

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

### 2. Comparação

Para cada planta baixada:
- Compara histogramas usando distância chi-quadrado
- Compara cor média
- Compara textura
- Calcula score médio normalizado (0-1)

### 3. Ranking

- Ordena plantas por score
- Retorna a melhor correspondência se score > 0.6
- Retorna top 3 alternativas

---

## 📈 Otimizações Futuras

### Curto Prazo
- [ ] Implementar extração real de features (TensorFlow.js)
- [ ] Adicionar cache de imagens das plantas
- [ ] Implementar sincronização incremental
- [ ] Adicionar compressão de dados

### Médio Prazo
- [ ] Treinar modelo ML customizado para PANCs
- [ ] Implementar busca por similaridade visual
- [ ] Adicionar reconhecimento de partes específicas (folha, flor, fruto)
- [ ] Suporte a identificação por múltiplas fotos

### Longo Prazo
- [ ] Modelo de IA on-device (CoreML/TFLite)
- [ ] Identificação em tempo real com câmera
- [ ] Compartilhamento de pacotes entre usuários
- [ ] Modo colaborativo de melhoria de dataset

---

## 🐛 Troubleshooting

### Problema: Plantas não baixam

**Solução:**
1. Verifique conexão de internet
2. Confirme que "Baixar apenas com WiFi" está desativado (se usando dados móveis)
3. Verifique espaço disponível no dispositivo
4. Tente limpar cache e baixar novamente

### Problema: Identificação offline não funciona

**Solução:**
1. Verifique se há plantas baixadas
2. Confirme que os dados da planta estão completos
3. Tente baixar novamente a planta
4. Verifique logs para erros de processamento

### Problema: Uso excessivo de armazenamento

**Solução:**
1. Acesse Configurações Offline
2. Reduza qualidade das fotos para "média" ou "baixa"
3. Desative "Incluir Modelos AR"
4. Ative "Limpar Plantas Antigas"
5. Remova plantas não utilizadas

---

## 📝 Notas Técnicas

### Armazenamento Local

- Usa AsyncStorage para metadados
- Cada planta tem chave única: `@planta_offline_{id}`
- Lista de plantas: `@plantas_offline_baixadas`
- Configurações: `@config_offline`

### Sincronização

- Status enviado ao servidor periodicamente
- Servidor mantém registro de plantas por usuário
- Permite análise de uso e recomendações

### Segurança

- Token de autenticação em todas as requisições
- Dados validados no backend
- Rate limiting para evitar abuso

---

## 👥 Contribuindo

Para contribuir com o sistema de plantas offline:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Implemente e teste
4. Envie um Pull Request

### Áreas de Contribuição

- Melhorias no algoritmo de identificação
- Novos pacotes de plantas
- Interface do usuário
- Documentação
- Testes

---

## 📄 Licença

Este projeto faz parte do sistema Colabora PANC.
Consulte o arquivo LICENSE principal do projeto para mais informações.

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Abra uma issue no GitHub
2. Consulte a documentação completa
3. Entre em contato com a equipe de desenvolvimento

---

**Desenvolvido com ❤️ para promover o conhecimento sobre PANCs (Plantas Alimentícias Não Convencionais)**
