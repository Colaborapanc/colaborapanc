import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import authService from '../services/authService';

export default function CadastroScreen({ navigation }) {
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);

  async function cadastrar() {
    if (!nome || !email || !senha) {
      Alert.alert("Campos obrigatórios", "Preencha todos os campos para cadastrar.");
      return;
    }
    setLoading(true);
    try {
      const resultado = await authService.register({ nome, email, username: email, password: senha });
      if (!resultado.sucesso) throw new Error(resultado.erro);
      Alert.alert("Conta criada", "Cadastro realizado com sucesso. Faça login!", [
        { text: "Ok", onPress: () => navigation.replace("Home") }
      ]);
    } catch (e) {
      Alert.alert("Erro ao cadastrar", String(e?.message || "Não foi possível criar sua conta."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: "#eafcf1" }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      <View style={styles.container}>
        <Text style={styles.logo}>🌱 Nova Conta</Text>
        <Text style={styles.slogan}>Preencha para participar do ColaboraPANC</Text>
        <TextInput
          placeholder="Nome completo"
          value={nome}
          onChangeText={setNome}
          style={styles.input}
        />
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
        <TouchableOpacity style={styles.botao} onPress={cadastrar} disabled={loading}>
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={{ color: "#fff", fontWeight: "700" }}>Cadastrar</Text>}
        </TouchableOpacity>
        <TouchableOpacity style={styles.link} onPress={() => navigation.navigate("Login")}>
          <Text style={{ color: "#188c54" }}>Já tem conta? Entrar</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center", padding: 26 },
  logo: { fontSize: 29, fontWeight: "bold", color: "#188c54", marginBottom: 10 },
  slogan: { color: "#50a477", fontWeight: "600", fontSize: 15, marginBottom: 23 },
  input: {
    width: "100%",
    backgroundColor: "#fff",
    borderRadius: 13,
    padding: 13,
    marginBottom: 11,
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
    marginTop: 6,
    marginBottom: 15
  },
  link: { marginTop: 2 }
});
