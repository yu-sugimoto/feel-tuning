// SignupScreen.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, ImageBackground, StyleSheet, Alert, TouchableOpacity, Dimensions } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';

const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;
const API_URL = Constants.expoConfig?.extra?.API_URL;

export default function SignupScreen() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSignup = async () => {
    try {
      const response = await fetch(`${API_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(err);
      }

      const data = await response.json();
      await AsyncStorage.setItem('accessToken', data.access_token);
      Alert.alert('登録成功');
      router.replace('/photo');
    } catch (error: any) {
      Alert.alert('登録失敗', error.message);
    }
  };

  return (
    <ImageBackground
      source={require('../assets/images/background.png')}
      style={styles.background}
      resizeMode="cover"
    >
      <View style={styles.container}>
        <Text style={styles.title}>アカウント作成</Text>

        <Text style={styles.label}>メールアドレス</Text>
        <TextInput
          style={styles.input}
          placeholder="メールアドレス入力"
          placeholderTextColor="#aaa"
          value={email}
          onChangeText={setEmail}
        />

        <Text style={styles.label}>パスワード</Text>
        <TextInput
          style={styles.input}
          placeholder="パスワード入力"
          placeholderTextColor="#aaa"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        <TouchableOpacity style={styles.button} onPress={handleSignup}>
          <Text style={styles.buttonText}>作成</Text>
        </TouchableOpacity>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  background: {
    width: screenWidth,
    height: screenHeight,
    justifyContent: "center",
    alignItems: "center",
  },
  container: {
    width: '60%',
    alignItems: 'center',
  },
  title: {
    fontSize: 38,
    color: "#fff",
    marginBottom: 40,
    fontWeight: "bold",
    textAlign: "center",
    bottom: 30,
  },
  label: {
    alignSelf: 'flex-start',
    color: '#fff',
    marginBottom: 5,
    marginTop: 10,
    fontWeight: 'bold',
  },
  input: {
    backgroundColor: '#444',
    color: '#fff',
    width: '100%',
    padding: 12,
    borderRadius: 5,
    marginBottom: 10,
    fontWeight: 'bold',
  },
  button: {
    backgroundColor: "#2C7FD5",
    padding: 16,
    borderColor: "white",
    borderWidth: 4,
    borderRadius: 10,
    marginTop: 100,
    minWidth: 330,
    alignItems: "center",
  },
  buttonText: {
    color: "white",
    fontSize: 35,
    fontWeight: "bold",
  },
});
