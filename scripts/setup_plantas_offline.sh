#!/bin/bash

echo "========================================="
echo "Setup: Sistema de Plantas Offline"
echo "========================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}1. Criando migrations para os novos modelos...${NC}"
python manage.py makemigrations mapping

echo -e "${YELLOW}2. Aplicando migrations ao banco de dados...${NC}"
python manage.py migrate

echo -e "${YELLOW}3. Coletando arquivos estáticos...${NC}"
python manage.py collectstatic --noinput || true

echo -e "${GREEN}✓ Backend configurado com sucesso!${NC}"

echo ""
echo -e "${YELLOW}4. Configurando mobile...${NC}"
cd mobile

if [ ! -d "node_modules" ]; then
    echo "Instalando dependências do mobile..."
    npm install
fi

echo "Instalando dependências adicionais..."
npm install @react-native-async-storage/async-storage
npm install @react-native-community/netinfo
npm install @react-native-community/slider

cd ..

echo -e "${GREEN}✓ Mobile configurado com sucesso!${NC}"

echo ""
echo "========================================="
echo -e "${GREEN}Setup Concluído!${NC}"
echo "========================================="
echo ""
echo "Próximos passos:"
echo "1. Configure o arquivo .env com suas credenciais"
echo "2. Execute: python manage.py runserver"
echo "3. No mobile, execute: cd mobile && npm start"
echo ""
echo "Documentação: docs/PLANTAS_OFFLINE_SELETIVAS.md"
echo ""
