import wikipedia
import re
import json
import os
from pathlib import Path

# Configurações
wikipedia.set_lang("pt")
CACHE_FILE = Path("/tmp/cache_wikipedia.json")  # Arquivo temporário

# Palavras-chave relacionadas à comestibilidade
PALAVRAS_COMESTIVEL = [
    "comestível", "comestiveis", "alimentício", "alimentar", "consumido", "consumida",
    "consumo humano", "utilizado na alimentação", "usado na culinária", "utilizado na culinária",
    "parte comestível", "edible", "used in cooking", "eaten", "used as food", "culinary use"
]

# Cache temporário para acelerar buscas
try:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
except FileNotFoundError:
    cache = {}

def verificar_comestibilidade(nome):
    nome_normalizado = nome.strip().lower()
    if nome_normalizado in cache:
        return cache[nome_normalizado]

    conteudo = None

    try:
        conteudo = wikipedia.page(nome).content.lower()
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            conteudo = wikipedia.page(e.options[0]).content.lower()
        except Exception:
            pass
    except wikipedia.exceptions.PageError:
        pass

    # Tenta em inglês se não encontrou nada em português
    if not conteudo:
        wikipedia.set_lang("en")
        try:
            conteudo = wikipedia.page(nome).content.lower()
        except:
            cache[nome_normalizado] = False
            return False
        finally:
            wikipedia.set_lang("pt")

    for termo in PALAVRAS_COMESTIVEL:
        if re.search(rf'\b{re.escape(termo)}\b', conteudo):
            cache[nome_normalizado] = True
            return True

    cache[nome_normalizado] = False
    return False

def salvar_cache_e_limpar():
    """Salva e depois remove o cache temporário."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    finally:
        if CACHE_FILE.exists():
            os.remove(CACHE_FILE)
