// app/login.tsx
import React, { useState } from 'react';
import { View, Text, TextInput, ImageBackground, StyleSheet, Alert, TouchableOpacity, Dimensions } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import Constants from 'expo-constants';

const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;
const API_URL = Constants.expoConfig?.extra?.API_URL;

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          username: email,
          password: password,
        }).toString(),
      });

      const data = await response.json();
      if (response.ok) {
        await AsyncStorage.setItem('accessToken', data.access_token);
        router.replace('/photo');
      } else {
        Alert.alert('ログイン失敗', data.detail || 'メールアドレスかパスワードが間違っています');
      }
    } catch (error) {
      Alert.alert('エラー', 'ログイン中にエラーが発生しました');
    }
  };

  return (
    <ImageBackground
      source={require('../assets/images/background.png')}
      style={styles.background}
      resizeMode="cover"
    >
      <View style={styles.container}>
        <Text style={styles.title}>ログイン</Text>

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

        <TouchableOpacity style={styles.button} onPress={handleLogin}>
          <Text style={styles.buttonText}>つづける</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button} onPress={() => {router.back()}}>
          <Text style={styles.buttonText}>もどる</Text>
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
    bottom: 50,
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
    marginTop: 50,
    minWidth: 330,
    alignItems: "center",
  },
  buttonText: {
    color: "white",
    fontSize: 35,
    fontWeight: "bold",
  },
});