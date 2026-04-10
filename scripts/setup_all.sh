#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> ColaboraPANC setup iniciado"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Erro: python3 não encontrado. Instale Python 3.9+ e tente novamente."
  exit 1
fi

if ! command -v pip3 >/dev/null 2>&1; then
  echo "Erro: pip3 não encontrado. Instale pip e tente novamente."
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Erro: node não encontrado. Instale Node.js 18+ e tente novamente."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Erro: npm não encontrado. Instale npm e tente novamente."
  exit 1
fi

if [ ! -f "${ROOT_DIR}/.env" ]; then
  if [ -f "${ROOT_DIR}/.env.example" ]; then
    echo "==> Copiando .env.example para .env"
    cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
  else
    echo "Aviso: .env.example não encontrado. Crie seu .env manualmente."
  fi
fi

if [ ! -d "${ROOT_DIR}/venv" ]; then
  echo "==> Criando virtualenv"
  python3 -m venv "${ROOT_DIR}/venv"
fi

# shellcheck disable=SC1091
source "${ROOT_DIR}/venv/bin/activate"

echo "==> Atualizando pip"
python -m pip install --upgrade pip

echo "==> Instalando dependências do backend"
pip install -r "${ROOT_DIR}/requirements.txt"

if [ -d "${ROOT_DIR}/mobile" ]; then
  echo "==> Instalando dependências do app mobile"
  (cd "${ROOT_DIR}/mobile" && npm install)
fi

echo "==> Setup concluído"

echo "\nPróximos passos (manuais):"
cat <<'NEXT'
- Configure o banco PostgreSQL/PostGIS e ajuste as variáveis POSTGRES_* no .env.
- Execute as migrações: python manage.py migrate
- Inicie o backend: python manage.py runserver
- Rode o app mobile: cd mobile && npm start
NEXT
