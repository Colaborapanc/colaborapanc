# Troubleshooting

## Backend não inicia: `DJANGO_SECRET_KEY não definido`
Defina `DJANGO_SECRET_KEY` no ambiente/.env.

## Erro de banco geoespacial
Sintoma: falhas com engine GIS/migrações.
- Verificar se o banco usa PostGIS.
- Confirmar extensão `postgis` ativa.

## Falha em inferência IA
- Verificar `PLANTNET_API_KEY` / `PLANTID_API_KEY`.
- Confirmar conectividade de rede para APIs externas.
- Validar formato de imagem enviado.

## Mobile não conecta na API
- Ajustar `EXPO_PUBLIC_API_URL`.
- Em dispositivo físico, não usar `localhost` da máquina host.

## Permissão negada em revisão científica
- Usuário precisa ser superusuário ou membro do grupo `Revisor`.
