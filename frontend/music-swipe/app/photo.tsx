// PhotoUploadScreen.tsx
import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert, ImageBackground, Dimensions } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { Linking } from 'react-native';
import Constants from 'expo-constants';


const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;
const API_URL = Constants.expoConfig?.extra?.API_URL;

export default function PhotoUploadScreen() {
  const router = useRouter();
  const [imageUri, setImageUri] = useState<string | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) {
        Alert.alert('認証エラー', 'ログインが必要です');
        router.replace('/login');
      }
    };
    checkAuth();
  }, []);

  const pickImage = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('許可が必要です', '写真ライブラリへのアクセスを許可してください');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
    }
  };

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert(
        '許可が必要です',
        'この機能を使用するには、設定からアクセスを許可してください',
        [
          { text: 'キャンセル', style: 'cancel' },
          { text: '設定を開く', onPress: () => Linking.openSettings() },
        ]
      );
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
    }
  };

  const sendImage = async () => {
    const token = await AsyncStorage.getItem('accessToken');
    if (!imageUri) return;

    const formData = new FormData();
    formData.append('file', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'photo.jpg',
    } as any);

    try {
      const res = await fetch(`${API_URL}/photo`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
        body: formData,
      });

      if (!res.ok) throw new Error(await res.text());

      Alert.alert('送信成功', '写真がアップロードされました');
      router.push('/');
    } catch (err: any) {
      Alert.alert('送信失敗', err.message);
    }
  };

  return (
    <ImageBackground
      source={require('../assets/images/background.png')}
      style={styles.background}
      resizeMode="cover"
    >
      <View style={styles.container}>
        <Text style={styles.title}>写真を送る</Text>
        <View style={styles.squareBox}>
          {imageUri ? (
            <Image source={{ uri: imageUri }} style={styles.image} />
          ) : (
            <Text style={styles.placeholder}>写真が選択されていません</Text>
          )}
        </View>

        <TouchableOpacity style={styles.cameraButton} onPress={takePhoto}>
          <Text style={styles.cameraButtonText}>カメラを起動</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.subButton} onPress={pickImage}>
          <Text style={styles.subButtonText}>写真を選択</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button} onPress={sendImage}>
          <Text style={styles.buttonText}>開始</Text>
        </TouchableOpacity>

        <View style={styles.navbar}>
          <TouchableOpacity style={[styles.navItem, styles.activeNavItem]}>
            <Image source={require("../assets/images/camera.png")} style={styles.icon} />
            <Text style={styles.activeNavText}>カメラ</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.navItem} onPress={() => router.push('/history')}>
            <Image source={require("../assets/images/history.png")} style={styles.icon} />
            <Text style={styles.navText}>履歴</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.navItem} onPress={() => router.push('/analysis')}>
            <Image source={require("../assets/images/analysis.png")} style={styles.icon} />
            <Text style={styles.navText}>分析</Text>
          </TouchableOpacity>
        </View>
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
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingBottom: 80,
  },
  title: {
    fontSize: 38,
    color: "#fff",
    marginBottom: 40,
    fontWeight: "bold",
    textAlign: "center",
  },
  squareBox: {
    width: 250,
    height: 250,
    backgroundColor: '#66c5f7',
    borderWidth: 2,
    borderColor: 'black',
    marginBottom: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholder: {
    color: 'white',
  },
  image: {
    width: 245,
    height: 245,
    resizeMode: 'cover',
  },
  subButton: {
    marginBottom: 12,
    backgroundColor: '#fff',
    paddingHorizontal: 28,
    paddingVertical: 8,
    borderRadius: 6,
  },
  subButtonText: {
    color: '#0078d7',
    fontWeight: 'bold',
    fontSize: 18,
  },
  button: {
    backgroundColor: "#2C7FD5",
    padding: 16,
    borderColor: "white",
    borderWidth: 4,
    borderRadius: 10,
    marginTop: 30,
    minWidth: 330,
    alignItems: "center",
  },
  buttonText: {
    color: "white",
    fontSize: 35,
    fontWeight: "bold",
  },
  cameraButton: {
    marginBottom: 12,
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 6,
  },
  cameraButtonText: {
    color: '#0078d7',
    fontWeight: 'bold',
    fontSize: 18,
  },
  navbar: {
    position: 'absolute',
    bottom: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    backgroundColor: '#ffffffcc',
    paddingVertical: 15,
  },
  navItem: {
    alignItems: 'center',
  },
  navText: {
    fontSize: 12,
  },
  activeNavText: {
    fontSize: 12,
    marginBottom: 10,
    fontWeight: 'bold',
    color: '#0078d7',
  },
  activeNavItem: {
    borderBottomWidth: 2,
    borderColor: '#0078d7',
    marginBottom: 20,
  },
  icon: {
    width: 36,
    height: 36,
    marginBottom: 5,
  },
});