#!/usr/bin/env bash
set -euo pipefail

FORCE=${FORCE:-0}
JOURNAL_VACUUM_DAYS=${JOURNAL_VACUUM_DAYS:-7}

if [[ ${EUID} -ne 0 ]]; then
  exec sudo --preserve-env=FORCE,JOURNAL_VACUUM_DAYS "$0" "$@"
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "Erro: apt-get não encontrado. Este script é destinado a sistemas Debian/Ubuntu." >&2
  exit 1
fi

if [[ "${FORCE}" != "1" ]]; then
  echo "Este script irá atualizar pacotes e remover dependências não utilizadas."
  echo "Use FORCE=1 para executar sem confirmação."
  read -r -p "Deseja continuar? [y/N] " response
  case "${response}" in
    [yY][eE][sS]|[yY])
      ;;
    *)
      echo "Operação cancelada."
      exit 0
      ;;
  esac
fi

echo "Atualizando lista de pacotes..."
apt-get update

echo "Atualizando pacotes instalados..."
apt-get -y upgrade

if apt-get -h | grep -q "full-upgrade"; then
  echo "Aplicando atualizações completas (full-upgrade)..."
  apt-get -y full-upgrade
fi

echo "Removendo pacotes e dependências não utilizadas..."
apt-get -y autoremove --purge

echo "Limpando cache do apt..."
apt-get -y autoclean
apt-get -y clean

if command -v journalctl >/dev/null 2>&1; then
  echo "Limpando logs do systemd (mantendo ${JOURNAL_VACUUM_DAYS} dias)..."
  journalctl --vacuum-time="${JOURNAL_VACUUM_DAYS}d" || true
fi

echo "Preparação concluída."
