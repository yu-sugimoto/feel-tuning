// SwipeScreen.tsx（安定性強化・音楽再生制御）
import React, { useEffect, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, Dimensions, TouchableOpacity, ImageBackground, Image
} from 'react-native';
import { Audio } from 'expo-av';
import { GestureHandlerRootView, GestureDetector, Gesture } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue, useAnimatedStyle, withSpring, withTiming, interpolate, runOnJS, Extrapolation
} from 'react-native-reanimated';
import { useRouter, useLocalSearchParams } from 'expo-router';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

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

export default function SwipeScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const [songs, setSongs] = useState<Song[]>([]);
  const [likeCount, setLikeCount] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [lastPlayedId, setLastPlayedId] = useState<number | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const scale = useSharedValue(1);

  useEffect(() => {
    if (params.songs) {
      try {
        const parsed = JSON.parse(params.songs as string);
        if (Array.isArray(parsed)) {
          setSongs(parsed);
        }
      } catch (err) {
        console.error("songs parse error:", err);
      }
    }
  }, [params.songs]);

  useEffect(() => {
    if (songs.length > 0 && songs[0].id !== lastPlayedId) {
      playSound(songs[0].url);
      setLastPlayedId(songs[0].id);
    }
    return () => {
      stopSound();
    };
  }, [songs]);

  const playSound = async (url: string) => {
    await stopSound();
    try {
      const { sound } = await Audio.Sound.createAsync({ uri: url }, { shouldPlay: true });
      soundRef.current = sound;
      setIsPlaying(true);
    } catch (err) {
      console.error("Sound error:", err);
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
    setIsPlaying(false);
  };

  const togglePlayback = async () => {
    if (soundRef.current) {
      const status = await soundRef.current.getStatusAsync();
      if (status.isLoaded) {
        if (status.isPlaying) {
          await soundRef.current.pauseAsync();
          setIsPlaying(false);
        } else {
          await soundRef.current.playAsync();
          setIsPlaying(true);
        }
      }
    }
  };

  const handleSwipe = async (liked: boolean) => {
    const current = songs[0];
    if (!current) return;

    try {
      const token = await AsyncStorage.getItem("accessToken");
      const res = await fetch(`${API_URL}/swipe`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ song_id: current.id, liked })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Swipe API failed");

      if (liked) {
        const newLikeCount = likeCount + 1;
        setLikeCount(newLikeCount);
        if (newLikeCount >= 5) {
          await stopSound();
          return router.push("/playlist");
        }
      }

      if (data.song && data.song.id !== current.id) {
        setSongs([data.song]);
      }
    } catch (err) {
      console.error("Swipe error:", err);
    } finally {
      resetCard();
    }
  };

  const resetCard = () => {
    translateX.value = 0;
    translateY.value = 0;
    scale.value = 1;
  };

  const gesture = Gesture.Pan()
    .onStart(() => {
      scale.value = withSpring(0.97);
    })
    .onUpdate((e) => {
      translateX.value = e.translationX;
      translateY.value = e.translationY;
    })
    .onEnd((e) => {
      scale.value = withSpring(1);
      if (e.translationX > screenWidth * 0.25) {
        translateX.value = withTiming(screenWidth);
        runOnJS(handleSwipe)(true);
      } else if (e.translationX < -screenWidth * 0.25) {
        translateX.value = withTiming(-screenWidth);
        runOnJS(handleSwipe)(false);
      } else {
        translateX.value = withSpring(0);
        translateY.value = withSpring(0);
      }
    });

  const cardStyle = useAnimatedStyle(() => {
    const rotate = interpolate(
      translateX.value,
      [-screenWidth / 2, 0, screenWidth / 2],
      [-15, 0, 15],
      Extrapolation.CLAMP
    );
    return {
      transform: [
        { translateX: translateX.value },
        { translateY: translateY.value },
        { scale: scale.value },
        { rotate: `${rotate}deg` },
      ]
    };
  });

  const current = songs[0];
  if (!current) {
    return (
      <ImageBackground
        source={require('../assets/images/background.png')}
        style={styles.background}
        resizeMode="cover"
      >
        <Text style={styles.title}>曲がありません</Text>
      </ImageBackground>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ImageBackground
        source={require('../assets/images/background.png')}
        style={styles.background}
        resizeMode="cover"
      >
        <Text style={styles.title}>❤️ {likeCount}/5</Text>
        <TouchableOpacity onPress={togglePlayback}>
          <Text style={styles.playStatus}>
            {isPlaying ? "▶️ 再生中" : "⏸️ 停止中（タップで再開）"}
          </Text>
        </TouchableOpacity>
        <GestureDetector gesture={gesture}>
          <Animated.View style={[styles.card, cardStyle]}>
            <Image source={require("../assets/images/cd.png")} style={styles.icon} />
            <Text style={styles.songTitle}>{current.title}</Text>
            <Text style={styles.artist}>{current.artist}</Text>
            <View style={styles.tags}>
              {Object.entries(current.tags).flatMap(([k, v]) =>
                v.map((tag, idx) => (
                  <Text key={`${k}-${idx}`} style={styles.tag}>#{tag}</Text>
                ))
              )}
            </View>
          </Animated.View>
        </GestureDetector>
      </ImageBackground>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  background: {
    width: screenWidth,
    height: screenHeight,
    justifyContent: 'center',
    alignItems: 'center'
  },
  title: {
    fontSize: 28,
    color: '#fff',
    marginTop: 40
  },
  playStatus: {
    fontSize: 18,
    color: '#eee',
    marginVertical: 10
  },
  card: {
    width: screenWidth * 0.8,
    height: screenHeight * 0.6,
    backgroundColor: 'white',
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30
  },
  icon: {
    width: 200,
    height: 200,
    resizeMode: 'contain',
    marginBottom: 20,
  },
  songTitle: {
    fontSize: 26,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333'
  },
  artist: {
    fontSize: 20,
    marginBottom: 20,
    color: '#555'
  },
  tags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center'
  },
  tag: {
    margin: 5,
    padding: 8,
    backgroundColor: '#2196F3',
    borderRadius: 15,
    color: 'white'
  }
});
