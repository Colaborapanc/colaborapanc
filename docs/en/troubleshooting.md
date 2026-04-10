# Troubleshooting

## Backend does not start: `DJANGO_SECRET_KEY não definido`
Set `DJANGO_SECRET_KEY` in environment/.env.

## Geospatial database error
Symptom: GIS engine/migrations failures.
- Check if the bank uses PostGIS.
- Confirm active `postgis` extension.

## AI inference failure
- Check `PLANTNET_API_KEY` / `PLANTID_API_KEY`.
- Confirm network connectivity for external APIs.
- Validate image format sent.

## Mobile does not connect to the API
- Adjust `EXPO_PUBLIC_API_URL`.
- On a physical device, do not use `localhost` from the host machine.

## Permission denied in scientific review
- User must be a superuser or member of the `Revisor` group.
