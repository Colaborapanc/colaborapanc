# Environment configuration

## Backend (`config/settings.py`)

| Variable | Mandatory | Usage |
|---|---:|---|
| `DJANGO_SECRET_KEY` | Yes | Django Secret Key |
| `DJANGO_DEBUG` | No | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | Yes (prod) | Allowed Hosts |
| `POSTGRES_DB` | Yes | Bank name |
| `POSTGRES_USER` | Yes | Bank user |
| `POSTGRES_PASSWORD` | Yes | Bank password |
| `POSTGRES_HOST` | Yes | Bank Host |
| `POSTGRES_PORT` | No | Bank door |
| `PLANTNET_API_KEY` | Optional* | PlantNet Inference |
| `PLANTID_API_KEY` | Optional* | Plant.id Inference |
| `CORS_ALLOWED_ORIGINS` | Recommended in prod | CORS Whitelist |

\* Without AI keys, inference functionalities are limited.

## Mobile
| Variable | Usage |
|---|---|
| `EXPO_PUBLIC_API_URL` | API base URL used by mobile services |

## Good practices
- Never commit `.env` with real secret.
- Use different values ​​for `dev`, `test` and `prod`.
- In production, `DEBUG=False`, explicit hosts/origins and secure cookies enabled.
