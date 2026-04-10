# Instalação do mobile (Expo)

## Requisitos
- Node.js 18+
- npm
- Expo CLI (via `npx expo` no fluxo atual)

## Passos
```bash
cd mobile
npm install
```

Crie `mobile/.env`:
```env
EXPO_PUBLIC_API_URL=http://localhost:8000
```

Inicie:
```bash
npm start
```

Atalhos:
- `npm run android`
- `npm run ios` (macOS)
- `npm run web`

## Ativação para dispositivo físico
1. Conecte o computador e o celular na mesma rede Wi‑Fi.
2. Troque `EXPO_PUBLIC_API_URL` para o IP local do backend, por exemplo:
   ```env
   EXPO_PUBLIC_API_URL=http://192.168.0.15:8000
   ```
3. Rode `npm start` e abra o app Expo Go no celular.
4. Escaneie o QR Code exibido no terminal.

## Testes recomendados (smoke test)
No diretório `mobile/`:
```bash
npm run test:ci
npx expo start --offline --clear
```

Checklist manual em dispositivo:
- Abrir tela inicial sem erro.
- Navegar entre telas principais.
- Validar chamada de API (lista/consulta) com backend local.
- Validar permissão de localização/câmera quando aplicável.
- Validar comportamento offline básico (sem travar UI).

## Troubleshooting
- **Erro `403 Forbidden` no `npm install`**: o ambiente pode estar bloqueando acesso ao `registry.npmjs.org`; configure um mirror liberado pela sua rede ou ajuste política do proxy corporativo.
- **API inacessível no celular**: confirme IP da máquina hospedeira e porta liberada no firewall.
- **Conflito de entrypoint**: o projeto possui `App.js` (React Navigation) e `index.tsx` (expo-router); padronize a estratégia de roteamento antes de publicar build.

## Upgrade controlado para SDK 54
No diretório `mobile/`, execute nesta ordem:

```bash
npm install
npx expo install --fix
npx expo-doctor@latest
npx expo start --clear
```

Checklist do upgrade:
- `expo-doctor` sem erro de schema no `app.json`.
- dependências core alinhadas (`expo`, `react-native`, `react`, `jest-expo`).
- Expo Go do dispositivo na mesma major do projeto (SDK 54).
