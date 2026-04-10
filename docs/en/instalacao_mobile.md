# Mobile installation (Expo)

## Requirements
- Node.js 18+
-npm
- Expo CLI (via `npx expo` in current stream)

## Steps
```bash
cd mobile
npm install
```

Create `mobile/.env`:
```env
EXPO_PUBLIC_API_URL=http://localhost:8000
```

Start:
```bash
npm start
```

Shortcuts:
- `npm run android`
- `npm run ios` (macOS)
- `npm run web`

## Activation for physical device
1. Connect your computer and cell phone to the same Wi‑Fi network.
2. Change `EXPO_PUBLIC_API_URL` to the local IP of the backend, for example:
   ```env
   EXPO_PUBLIC_API_URL=http://192.168.0.15:8000
   ```
3. Run `npm start` and open the Expo Go app on your phone.
4. Scan the QR Code displayed on the terminal.

## Recommended tests (smoke test)
In the `mobile/` directory:
```bash
npm run test:ci
npx expo start --offline --clear
```

Manual checklist on device:
- Open home screen without error.
- Navigate between main screens.
- Validate (lista/consulta) API call with local backend.
- Validate location/camera permission when applicable.
- Validate basic offline behavior (without UI crash).

## Troubleshooting
- **Error `403 Forbidden` in `npm install`**: the environment may be blocking access to `registry.npmjs.org`; configure a mirror released by your network or adjust corporate proxy policy.
- **API inaccessible on cell phones**: confirm IP of the host machine and port released on the firewall.
- **Entrypoint conflict**: the project has `App.js` (React Navigation) and `index.tsx` (expo-router); Standardize the routing strategy before publishing build.

## Controlled upgrade to SDK 54
In the `mobile/` directory, run in this order:

```bash
npm install
npx expo install --fix
npx expo-doctor@latest
npx expo start --clear
```

Upgrade checklist:
- `expo-doctor` no schema error in `app.json`.
- aligned core dependencies (`expo`, `react-native`, `react`, `jest-expo`).
- Device Expo Go in the same project major (SDK 54).
