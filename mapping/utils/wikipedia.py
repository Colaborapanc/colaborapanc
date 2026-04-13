import re
import json
import os
from pathlib import Path
from threading import Lock
import wikipedia

# Configura idioma padrão (é redefinido a cada chamada para segurança)
CACHE_FILE = Path("/tmp/cache_wikipedia.json")
PALAVRAS_COMESTIVEL = [
    "comestível", "comestiveis", "alimentício", "alimentar", "consumido", "consumida",
    "consumo humano", "utilizado na alimentação", "usado na culinária", "utilizado na culinária",
    "parte comestível", "edible", "used in cooking", "eaten", "used as food", "culinary use"
]

cache_lock = Lock()
try:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    cache = {}

def verificar_comestibilidade(nome):
    nome_normalizado = nome.strip().lower()
    with cache_lock:
        if nome_normalizado in cache:
            return cache[nome_normalizado]

    conteudo = buscar_conteudo_wikipedia(nome, lang="pt") or buscar_conteudo_wikipedia(nome, lang="en")

    resultado = any(re.search(rf'\b{re.escape(termo)}\b', conteudo) for termo in PALAVRAS_COMESTIVEL) if conteudo else False

    with cache_lock:
        cache[nome_normalizado] = resultado
    return resultado

def buscar_conteudo_wikipedia(nome, lang="pt"):
    wikipedia.set_lang(lang)
    try:
        return wikipedia.page(nome).content.lower()
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            return wikipedia.page(e.options[0]).content.lower()
        except:
            return None
    except wikipedia.exceptions.PageError:
        return None
    except:
        return None

def salvar_cache_e_limpar():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Erro] Falha ao salvar cache: {e}")
    finally:
        if CACHE_FILE.exists():
            os.remove(CACHE_FILE)
