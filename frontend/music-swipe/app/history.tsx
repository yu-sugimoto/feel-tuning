import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ImageBackground, Dimensions, TouchableOpacity, Image, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;
const API_URL = Constants.expoConfig?.extra?.API_URL;

interface PlaylistHistory {
  id: number;
  image_path: string;
  songs_json: string;
  created_at: string;
}

export default function HistoryScreen() {
  const router = useRouter();
  const [history, setHistory] = useState<PlaylistHistory[]>([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = await AsyncStorage.getItem("accessToken");
        const res = await fetch(`${API_URL}/history`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        setHistory(data);
      } catch (err) {
        console.error("履歴取得エラー:", err);
      }
    };
    fetchHistory();
  }, []);

  return (
    <ImageBackground
      source={require('../assets/images/background.png')}
      style={styles.background}
      resizeMode="cover"
    >
      <View style={styles.container}>
        <Text style={styles.title}>履歴</Text>

        {history.length === 0 ? (
          <Text style={styles.noHistory}>履歴はまだありません</Text>
        ) : (
          <ScrollView contentContainerStyle={styles.scroll}>
            {history.map((item) => (
              <View key={item.id} style={styles.card}>
                <Text style={styles.date}>{new Date(item.created_at).toLocaleString()}</Text>
                <Text numberOfLines={1} style={styles.songCount}>
                  曲数: {JSON.parse(item.songs_json).length}
                </Text>
              </View>
            ))}
          </ScrollView>
        )}

        <View style={styles.navbar}>
          <TouchableOpacity style={styles.navItem} onPress={() => router.push('/photo')}>
            <Image source={require("../assets/images/camera.png")} style={styles.icon} />
            <Text style={styles.navText}>カメラ</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.navItem, styles.activeNavItem]}>
            <Image source={require("../assets/images/history.png")} style={styles.icon} />
            <Text style={styles.activeNavText}>履歴</Text>
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
    paddingTop: 60,
    alignItems: 'center',
    width: '100%',
    paddingBottom: 80,
  },
  title: {
    fontSize: 26,
    color: '#fff',
    fontWeight: 'bold',
    marginBottom: 10,
  },
  noHistory: {
    fontSize: 18,
    color: '#ccc',
    marginTop: 30,
  },
  scroll: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  card: {
    backgroundColor: '#ffffffcc',
    borderRadius: 15,
    padding: 15,
    marginVertical: 10,
    width: screenWidth * 0.85,
  },
  date: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  songCount: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
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
