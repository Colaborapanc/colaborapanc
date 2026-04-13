# mapping/utils_alertas.py

import unicodedata

# Dicionário de tipos de alerta para URLs de ícones
TIPOS_ALERTA_ICONES = {
    "chuva forte": "https://cdn-icons-png.flaticon.com/512/4005/4005901.png",
    "vento forte": "https://cdn-icons-png.flaticon.com/512/1812/1812660.png",
    "calor intenso": "https://cdn-icons-png.flaticon.com/512/1684/1684375.png",
    "geada": "https://cdn-icons-png.flaticon.com/512/818/818600.png",
    "incendio florestal": "https://cdn-icons-png.flaticon.com/512/3845/3845781.png",
    "incêndio florestal": "https://cdn-icons-png.flaticon.com/512/3845/3845781.png",
    "granizo": "https://cdn-icons-png.flaticon.com/512/1518/1518943.png",
    "alagamento": "https://cdn-icons-png.flaticon.com/512/2698/2698577.png",
    "frio intenso": "https://cdn-icons-png.flaticon.com/512/1724/1724681.png",
    "seca": "https://cdn-icons-png.flaticon.com/512/2722/2722737.png",
    "tempestade": "https://cdn-icons-png.flaticon.com/512/890/890347.png",
    # Adicione outros tipos e ícones conforme necessidade
}

ICONE_PADRAO = "https://cdn-icons-png.flaticon.com/512/992/992700.png"  # ícone padrão feliz/safe

def normalizar_tipo_alerta(tipo):
    """Normaliza o texto do tipo de alerta para facilitar o match no dicionário."""
    if not tipo:
        return ""
    tipo = tipo.strip().lower()
    # Remove acentos
    tipo = unicodedata.normalize('NFKD', tipo)
    tipo = "".join([c for c in tipo if not unicodedata.combining(c)])
    return tipo

def get_icone_alerta(tipo):
    """
    Retorna a URL do ícone correspondente ao tipo de alerta.
    Usa ícone padrão se não encontrado.
    """
    tipo_norm = normalizar_tipo_alerta(tipo)
    return TIPOS_ALERTA_ICONES.get(tipo_norm, ICONE_PADRAO)
