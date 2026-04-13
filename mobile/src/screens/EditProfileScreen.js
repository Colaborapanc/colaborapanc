import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import { API_ENDPOINTS } from '../config/api';
import api from '../services/apiClient';

export default function EditProfileScreen({ navigation }) {
  const [nome, setNome] = useState('');
  const [bio, setBio] = useState('');
  const [loading, setLoading] = useState(false);

  const salvarPerfil = async () => {
    setLoading(true);
    try {
      await api.put(API_ENDPOINTS.perfil, { nome, bio });
      Alert.alert('Sucesso', 'Perfil atualizado com sucesso!', [{ text: 'OK', onPress: () => navigation.goBack() }]);
    } catch (error) {
      console.error('Erro ao salvar perfil:', error);
      Alert.alert('Erro', error?.message || 'Não foi possível salvar o perfil. Verifique login/permissões.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.formContainer}>
        <Text style={styles.title}>Editar Perfil</Text>

        <View style={styles.inputContainer}>
          <MaterialIcons name="person" size={24} color="#666" style={styles.inputIcon} />
          <TextInput style={styles.input} placeholder="Nome" value={nome} onChangeText={setNome} maxLength={100} />
        </View>

        <View style={styles.inputContainer}>
          <MaterialIcons name="description" size={24} color="#666" style={styles.inputIcon} />
          <TextInput style={[styles.input, styles.bioInput]} placeholder="Bio" value={bio} onChangeText={setBio} multiline numberOfLines={4} maxLength={500} />
        </View>

        <TouchableOpacity style={[styles.saveButton, loading && styles.disabledButton]} onPress={salvarPerfil} disabled={loading}>
          <Text style={styles.saveButtonText}>{loading ? 'Salvando...' : 'Salvar Alterações'}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  formContainer: { padding: 20 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#333', marginBottom: 30, textAlign: 'center' },
  inputContainer: { flexDirection: 'row', alignItems: 'flex-start', backgroundColor: '#fff', borderRadius: 10, marginBottom: 20, paddingHorizontal: 15, paddingVertical: 12, elevation: 2, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.2, shadowRadius: 2 },
  inputIcon: { marginRight: 10, marginTop: 2 },
  input: { flex: 1, fontSize: 16, color: '#333' },
  bioInput: { minHeight: 100, textAlignVertical: 'top' },
  saveButton: { backgroundColor: '#4CAF50', borderRadius: 10, padding: 15, alignItems: 'center', marginTop: 20 },
  disabledButton: { backgroundColor: '#999' },
  saveButtonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
