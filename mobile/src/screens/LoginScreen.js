import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import authService from '../services/authService';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);

  async function realizarLogin() {
    if (!email || !senha) {
      Alert.alert("Campos obrigatórios", "Preencha email e senha para continuar.");
      return;
    }
    setLoading(true);
    try {
      const resultado = await authService.login({ username: email, password: senha });
      if (!resultado.sucesso) throw new Error(resultado.erro);
      navigation.replace('Home');
    } catch (e) {
      Alert.alert("Erro ao entrar", String(e?.message || "Confira seus dados e tente novamente."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: "#eafcf1" }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <View style={styles.container}>
        <Text style={styles.logo}>🌿 ColaboraPANC</Text>
        <Text style={styles.slogan}>Mapa colaborativo das PANCs do Brasil</Text>
        <TextInput
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          autoCapitalize="none"
          keyboardType="email-address"
          autoCorrect={false}
        />
        <TextInput
          placeholder="Senha"
          value={senha}
          onChangeText={setSenha}
          style={styles.input}
          secureTextEntry
        />
        <TouchableOpacity style={styles.botao} onPress={realizarLogin} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={{ color: "#fff", fontWeight: "700" }}>Entrar</Text>}
        </TouchableOpacity>
        <TouchableOpacity style={styles.link} onPress={() => navigation.navigate("Cadastro")}>
          <Text style={{ color: "#188c54" }}>Criar uma conta</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center", padding: 26 },
  logo: { fontSize: 32, fontWeight: "bold", color: "#188c54", marginBottom: 12 },
  slogan: { color: "#50a477", fontWeight: "600", fontSize: 15, marginBottom: 26 },
  input: {
    width: "100%",
    backgroundColor: "#fff",
    borderRadius: 13,
    padding: 13,
    marginBottom: 12,
    fontSize: 16,
    borderColor: "#b9f1c6",
    borderWidth: 1.4
  },
  botao: {
    width: "100%",
    backgroundColor: "#27ae60",
    borderRadius: 14,
    padding: 14,
    alignItems: "center",
    marginTop: 8,
    marginBottom: 16
  },
  link: { marginTop: 5 }
});
