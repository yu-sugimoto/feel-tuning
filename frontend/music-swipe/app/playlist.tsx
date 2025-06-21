import React, { useEffect, useState, useRef } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity, Dimensions, Image
} from 'react-native';
import { Audio } from 'expo-av';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming
} from 'react-native-reanimated';

const screenWidth = Dimensions.get('window').width;
const screenHeight = Dimensions.get('window').height;
const API_URL = Constants.expoConfig?.extra?.API_URL;

interface Song {
  id: number;
  title: string;
  artist: string;
  url: string;
  tags: {
    genres: string[];
    instruments: string[];
    vartags: string[];
  };
}

interface PlaylistResponse {
  liked: Song[];
  recommended: Song[];
}

export default function PlaylistScreen() {
  const router = useRouter();
  const [liked, setLiked] = useState<Song[]>([]);
  const [recommended, setRecommended] = useState<Song[]>([]);
  const [playingId, setPlayingId] = useState<number | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

  const dot1 = useSharedValue(0);
  const dot2 = useSharedValue(0);
  const dot3 = useSharedValue(0);

  const dot1Style = useAnimatedStyle(() => ({
    transform: [{ translateY: dot1.value }],
  }));
  const dot2Style = useAnimatedStyle(() => ({
    transform: [{ translateY: dot2.value }],
  }));
  const dot3Style = useAnimatedStyle(() => ({
    transform: [{ translateY: dot3.value }],
  }));

  useEffect(() => {
    const fetchPlaylist = async () => {
      try {
        const token = await AsyncStorage.getItem('accessToken');
        const res = await fetch(`${API_URL}/playlist`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || '取得失敗');
        }
        const data: PlaylistResponse = await res.json();
        setLiked(data.liked);
        setRecommended(data.recommended);
      } catch (err) {
        console.error('[ERROR] プレイリスト取得失敗:', err);
      }
    };
    fetchPlaylist();

    return () => {
      stopSound();
    };
  }, []);

  const playSound = async (song: Song) => {
    await stopSound();
    try {
      const { sound } = await Audio.Sound.createAsync({ uri: song.url });
      soundRef.current = sound;
      await sound.playAsync();
      setPlayingId(song.id);
      startAnimation();
    } catch (err) {
      console.error('[ERROR] 再生失敗:', err);
    }
  };

  const stopSound = async () => {
    if (soundRef.current) {
      try {
        await soundRef.current.stopAsync();
        await soundRef.current.unloadAsync();
      } catch {}
      soundRef.current = null;
    }
    setPlayingId(null);
  };

  const startAnimation = () => {
    dot1.value = withRepeat(withTiming(-5, { duration: 400 }), -1, true);
    dot2.value = withRepeat(withTiming(-10, { duration: 400 }), -1, true);
    dot3.value = withRepeat(withTiming(-7, { duration: 400 }), -1, true);
  };

  const renderSong = (song: Song) => {
    const isPlaying = playingId === song.id;

    return (
      <View style={styles.card}>
        <Text style={styles.title}>{song.title}</Text>
        <Text style={styles.artist}>{song.artist}</Text>
        <View style={styles.tags}>
          {Object.entries(song.tags).flatMap(([k, v]) =>
            v.map((tag, i) => (
              <Text key={`${k}-${i}`} style={styles.tag}>#{tag}</Text>
            ))
          )}
        </View>
        <TouchableOpacity
          onPress={() => (isPlaying ? stopSound() : playSound(song))}
          style={styles.button}
        >
          <Text style={styles.buttonText}>
            {isPlaying ? '⏹ 停止' : '▶️ 再生'}
          </Text>
        </TouchableOpacity>

        {isPlaying && (
          <View style={styles.indicator}>
            <Animated.View style={[styles.dot, dot1Style]} />
            <Animated.View style={[styles.dot, dot2Style]} />
            <Animated.View style={[styles.dot, dot3Style]} />
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.section}>❤️ Likeした曲</Text>
      <FlatList
        data={liked}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => renderSong(item)}
        horizontal
        showsHorizontalScrollIndicator={false}
      />
      <Text style={styles.section}>🎧 あなたにおすすめ</Text>
      <FlatList
        data={recommended}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => renderSong(item)}
        horizontal
        showsHorizontalScrollIndicator={false}
      />

      <View style={styles.navbar}>
        <TouchableOpacity style={[styles.navItem, styles.activeNavItem]} onPress={() => router.push('/photo')}>
          <Image source={require("../assets/images/camera.png")} style={styles.icon} />
          <Text style={styles.activeNavText}>カメラ</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => router.push('/history')}>
          <Image source={require("../assets/images/history.png")} style={styles.icon} />
          <Text style={styles.navText}>履歴</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem}>
          <Image source={require("../assets/images/analysis.png")} style={styles.icon} />
          <Text style={styles.navText}>分析</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 50,
    backgroundColor: '#f5f5f5',
    flex: 1,
    paddingBottom: 90,
  },
  section: {
    fontSize: 22,
    fontWeight: 'bold',
    marginLeft: 20,
    marginTop: 20,
    marginBottom: 10,
  },
  card: {
    width: screenWidth * 0.7,
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 20,
    marginHorizontal: 10,
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 5,
  },
  artist: {
    fontSize: 16,
    color: '#555',
    marginBottom: 10,
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginBottom: 10,
  },
  tag: {
    margin: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#2196F3',
    borderRadius: 12,
    color: 'white',
    fontSize: 12,
  },
  button: {
    marginTop: 10,
    backgroundColor: '#4CAF50',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 25,
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  indicator: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 6,
    height: 20,
  },
  dot: {
    width: 6,
    height: 6,
    backgroundColor: '#4CAF50',
    borderRadius: 3,
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
