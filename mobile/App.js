import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer, CommonActions, createNavigationContainerRef } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { LogBox } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import HomeScreen from './src/screens/HomeScreen';
import LoginScreen from './src/screens/LoginScreen';
import CadastroScreen from './src/screens/CadastroScreen';
import MapScreen from './src/screens/MapScreen';
import CadastroPontoScreen from './src/screens/CadastroPontoScreen';
import DetalhePontoScreen from './src/screens/DetalhePontoScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import EditProfileScreen from './src/screens/EditProfileScreen';
import RevisorScreen from './src/screens/RevisorScreen';
import SplashScreen from './src/screens/SplashScreen';
import NotificacoesScreen from './src/screens/NotificacoesScreen';
import PlantasOfflineScreen from './src/screens/PlantasOfflineScreen';
import MinhasPlantasOfflineScreen from './src/screens/MinhasPlantasOfflineScreen';
import IdentificarPlantaScreen from './src/screens/IdentificarPlantaScreen';
import offlineService from './src/services/offlineService';
import { getAuthToken, setAuthToken, subscribeAuthToken, subscribeUnauthorized } from './src/services/httpClient';

LogBox.ignoreLogs(['Invalid prop `style` supplied to `React.Fragment`']);

const Stack = createStackNavigator();
const navigationRef = createNavigationContainerRef();

export default function App() {
  const [authLoading, setAuthLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const bootstrapAuth = async () => {
      try {
        const token = await getAuthToken();
        if (token && !String(token).startsWith('session:')) {
          await setAuthToken(token);
          setIsAuthenticated(true);
        } else {
          if (token && String(token).startsWith('session:')) {
            await setAuthToken(null);
          }
          setIsAuthenticated(false);
        }
      } finally {
        setAuthLoading(false);
      }
    };

    bootstrapAuth();

    const unsubscribe = subscribeAuthToken((token) => {
      setIsAuthenticated(!!token);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    const unsubscribeUnauthorized = subscribeUnauthorized(async () => {
      await AsyncStorage.removeItem('userId');
      setIsAuthenticated(false);
      if (navigationRef.isReady()) {
        navigationRef.dispatch(CommonActions.reset({ index: 0, routes: [{ name: 'Login' }] }));
      }
    });
    return unsubscribeUnauthorized;
  }, []);

  useEffect(() => {
    offlineService.setUnauthorizedHandler(async () => {
      await setAuthToken(null);
      await AsyncStorage.removeItem('userId');
      setIsAuthenticated(false);
      if (navigationRef.isReady()) {
        navigationRef.dispatch(CommonActions.reset({ index: 0, routes: [{ name: 'Login' }] }));
      }
    });
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      offlineService.pararSincronizacaoAutomatica();
      return undefined;
    }
    const disposeSync = offlineService.configurarSincronizacaoAutomatica(10);
    return () => {
      if (typeof disposeSync === 'function') disposeSync();
    };
  }, [isAuthenticated]);

  const commonOptions = useMemo(() => ({
    headerStyle: { backgroundColor: '#4CAF50' },
    headerTintColor: '#fff',
    headerTitleStyle: { fontWeight: 'bold' },
  }), []);

  if (authLoading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f4fcf7' }}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  return (
    <NavigationContainer ref={navigationRef}>
      <Stack.Navigator key={isAuthenticated ? 'auth' : 'guest'} initialRouteName={isAuthenticated ? 'Home' : 'Login'} screenOptions={commonOptions}>
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'ColaboraPANC' }} />
        <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'Login' }} />
        <Stack.Screen name="Cadastro" component={CadastroScreen} options={{ title: 'Criar Conta' }} />
        <Stack.Screen name="Mapa" component={MapScreen} options={{ title: 'Mapa de PANCs' }} />
        <Stack.Screen name="CadastroPonto" component={CadastroPontoScreen} options={{ title: 'Cadastrar PANC' }} />
        <Stack.Screen name="DetalhePonto" component={DetalhePontoScreen} options={{ title: 'Detalhes da PANC' }} />
        <Stack.Screen name="Perfil" component={ProfileScreen} options={{ title: 'Meu Perfil' }} />
        <Stack.Screen name="EditarPerfil" component={EditProfileScreen} options={{ title: 'Editar Perfil' }} />
        <Stack.Screen name="Revisor" component={RevisorScreen} options={{ title: 'Painel Revisor' }} />
        <Stack.Screen name="Notificacoes" component={NotificacoesScreen} options={{ title: 'Notificações' }} />
        <Stack.Screen name="PlantasOffline" component={PlantasOfflineScreen} options={{ title: 'Base Offline de Espécies' }} />
        <Stack.Screen name="MinhasPlantas" component={MinhasPlantasOfflineScreen} options={{ title: 'Minhas Espécies Offline' }} />
        <Stack.Screen name="IdentificarPlanta" component={IdentificarPlantaScreen} options={{ title: 'Detecção por Câmera' }} />
        <Stack.Screen name="Splash" component={SplashScreen} options={{ headerShown: false }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
