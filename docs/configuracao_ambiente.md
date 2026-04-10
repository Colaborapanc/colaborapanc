# Configuração de ambiente

## Backend (`config/settings.py`)

| Variável | Obrigatória | Uso |
|---|---:|---|
| `DJANGO_SECRET_KEY` | Sim | Chave secreta do Django |
| `DJANGO_DEBUG` | Não | Modo debug |
| `DJANGO_ALLOWED_HOSTS` | Sim (prod) | Hosts permitidos |
| `POSTGRES_DB` | Sim | Nome do banco |
| `POSTGRES_USER` | Sim | Usuário do banco |
| `POSTGRES_PASSWORD` | Sim | Senha do banco |
| `POSTGRES_HOST` | Sim | Host do banco |
| `POSTGRES_PORT` | Não | Porta do banco |
| `PLANTNET_API_KEY` | Opcional* | Inferência PlantNet |
| `PLANTID_API_KEY` | Opcional* | Inferência Plant.id |
| `CORS_ALLOWED_ORIGINS` | Recomendado em prod | Whitelist de CORS |

\* Sem chaves de IA, funcionalidades de inferência ficam limitadas.

## Mobile
| Variável | Uso |
|---|---|
| `EXPO_PUBLIC_API_URL` | URL base da API usada pelos serviços mobile |

## Boas práticas
- Nunca commitar `.env` com segredo real.
- Usar valores diferentes para `dev`, `test` e `prod`.
- Em produção, `DEBUG=False`, hosts/origens explícitos e cookies seguros habilitados.
