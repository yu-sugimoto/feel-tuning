import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ImageBackground, Dimensions, Alert } from 'react-native';
import { GestureHandlerRootView, Gesture, GestureDetector } from 'react-native-gesture-handler';
import Animated, { 
  useSharedValue, 
  useAnimatedStyle, 
  runOnJS,
  interpolate,
  withSpring,
  withTiming,
  Extrapolation
} from 'react-native-reanimated';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter, useLocalSearchParams } from 'expo-router';
import Constants from 'expo-constants';

const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;
const API_URL = Constants.expoConfig?.extra?.API_URL;

interface Song {
  id: number;
  title: string;
  artists: string;
  tags: string[];
}

// Mock data for testing
const MOCK_SONGS: Song[] = [
  {
    id: 1,
    title: "夏の終わり",
    artists: "森高千里",
    tags: ["夏", "ノスタルジック", "ポップス"]
  },
  {
    id: 2,
    title: "津軽海峡冬景色",
    artists: "石川さゆり",
    tags: ["冬", "演歌", "しっとり"]
  },
  {
    id: 3,
    title: "青春",
    artists: "毛皮のマリーズ",
    tags: ["青春", "ロック", "エネルギッシュ"]
  },
  {
    id: 4,
    title: "桜坂",
    artists: "福山雅治",
    tags: ["春", "バラード", "切ない"]
  },
  {
    id: 5,
    title: "クリスマスソング",
    artists: "back number",
    tags: ["冬", "クリスマス", "恋愛"]
  }
];

const SWIPE_THRESHOLD = screenWidth * 0.3;

export default function SwipeScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const [songQueue, setSongQueue] = useState<Song[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [likeCount, setLikeCount] = useState(0);

  // Animation values
  const translateX = useSharedValue(0);
  const translateY = useSharedValue(0);
  const scale = useSharedValue(1);

  // Reset animation values safely
  const resetAnimation = () => {
    translateX.value = 0;
    translateY.value = 0;
    scale.value = 1;
  };

  useEffect(() => {
    // Photo画面から渡された楽曲リストを取得
    if (params.songs) {
      try {
        const songs = JSON.parse(params.songs as string) as Song[];
        if (songs.length > 0) {
          setSongQueue(songs);
          return;
        }
      } catch (error) {
        console.error('楽曲データの解析に失敗:', error);
      }
    }
    
    // APIデータがない場合はMockデータを使用
    setSongQueue(MOCK_SONGS);
  }, [params.songs]);

  const handleSwipe = async (liked: boolean) => {
    const currentSong = songQueue[0];
    if (!currentSong) return;

    // Like数をカウント
    if (liked) {
      const newLikeCount = likeCount + 1;
      setLikeCount(newLikeCount);
      
      // 3曲Likeで終了
      if (newLikeCount >= 3) {
        Alert.alert('完了', 'Swipeありがとうございました！\n3曲の楽曲を見つけました🎵', [
          { text: 'OK', onPress: () => router.push('/photo') }
        ]);
        return;
      }
    }

    setIsLoading(true);

    // Mock mode: Use local data if no API_URL or using mock data
    const usingMockData = !params.songs || songQueue === MOCK_SONGS;
    if (!API_URL || usingMockData) {
      // Simulate API delay
      setTimeout(() => {
        const newQueue = songQueue.slice(1);
        setSongQueue(newQueue);
        resetAnimation();
        if (newQueue.length === 0) {
          Alert.alert('完了', 'すべての楽曲をスワイプしました！', [
            { text: 'OK', onPress: () => router.push('/photo') }
          ]);
        }
        setIsLoading(false);
      }, 800);
      return;
    }

    // Real API call
    const token = await AsyncStorage.getItem('accessToken');

    try {
      const response = await fetch(`${API_URL}/swipe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          song_id: currentSong.id,
          liked: liked,
        }),
      });

      const data = await response.json();
      
      if (response.ok && data.song) {
        // 現在の曲を削除し、APIから受け取った新しい曲を追加
        const newQueue = songQueue.slice(1);
        newQueue.push(data.song);
        setSongQueue(newQueue);
        resetAnimation();
      } else if (response.status === 404) {
        // スワイプ候補なし - 現在の曲だけ削除
        const newQueue = songQueue.slice(1);
        setSongQueue(newQueue);
        resetAnimation();
        
        if (newQueue.length === 0) {
          Alert.alert('完了', 'すべての楽曲をスワイプしました！', [
            { text: 'OK', onPress: () => router.push('/photo') }
          ]);
        }
      } else {
        throw new Error(data.detail || 'スワイプに失敗しました');
      }
    } catch (error: any) {
      Alert.alert('エラー', error.message);
      // エラー時も現在の曲は削除して続行
      const newQueue = songQueue.slice(1);
      setSongQueue(newQueue);
      resetAnimation();
    } finally {
      setIsLoading(false);
    }
  };

  const panGesture = Gesture.Pan()
    .onStart(() => {
      scale.value = withSpring(0.95);
    })
    .onUpdate((event) => {
      translateX.value = event.translationX;
      translateY.value = event.translationY;
    })
    .onEnd((event) => {
      const shouldSwipeRight = event.translationX > SWIPE_THRESHOLD;
      const shouldSwipeLeft = event.translationX < -SWIPE_THRESHOLD;

      scale.value = withSpring(1);

      if (shouldSwipeRight || shouldSwipeLeft) {
        // Animate card out of screen
        translateX.value = withTiming(shouldSwipeRight ? screenWidth : -screenWidth, { duration: 300 });
        translateY.value = withTiming(event.translationY + event.velocityY * 0.1, { duration: 300 });
        
        // Trigger swipe action
        runOnJS(handleSwipe)(shouldSwipeRight);
      } else {
        // Spring back to center
        translateX.value = withSpring(0);
        translateY.value = withSpring(0);
      }
    });

  const cardStyle = useAnimatedStyle(() => {
    const rotation = interpolate(
      translateX.value,
      [-screenWidth / 2, 0, screenWidth / 2],
      [-15, 0, 15],
      Extrapolation.CLAMP
    );

    const opacity = interpolate(
      Math.abs(translateX.value),
      [0, SWIPE_THRESHOLD],
      [1, 0.8],
      Extrapolation.CLAMP
    );

    return {
      transform: [
        { translateX: translateX.value },
        { translateY: translateY.value },
        { rotate: `${rotation}deg` },
        { scale: scale.value },
      ],
      opacity,
    };
  });

  const likeOverlayStyle = useAnimatedStyle(() => {
    const opacity = interpolate(
      translateX.value,
      [0, SWIPE_THRESHOLD],
      [0, 1],
      Extrapolation.CLAMP
    );

    return {
      opacity,
    };
  });

  const dislikeOverlayStyle = useAnimatedStyle(() => {
    const opacity = interpolate(
      translateX.value,
      [-SWIPE_THRESHOLD, 0],
      [1, 0],
      Extrapolation.CLAMP
    );

    return {
      opacity,
    };
  });

  const currentSong = songQueue[0];
  const nextSong = songQueue[1];

  if (!currentSong) {
    return (
      <ImageBackground
        source={require('../assets/images/background.png')}
        style={styles.background}
        resizeMode="cover"
      >
        <View style={styles.container}>
          <Text style={styles.title}>楽曲を読み込み中...</Text>
        </View>
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
        <View style={styles.container}>
          <Text style={styles.title}>楽曲スワイプ</Text>
          <Text style={styles.likeCounter}>❤️ {likeCount}/3</Text>
          
          <View style={styles.cardContainer}>
            {/* Next card (background) */}
            {nextSong && (
              <View style={[styles.musicCard, styles.nextCard]}>
                <Text style={styles.songTitle}>{nextSong.title}</Text>
                <Text style={styles.artistName}>{nextSong.artists}</Text>
              </View>
            )}

            {/* Current card (foreground) */}
            <GestureDetector gesture={panGesture}>
              <Animated.View style={[styles.musicCard, cardStyle]}>
                {/* Like overlay */}
                <Animated.View style={[styles.overlay, styles.likeOverlay, likeOverlayStyle]}>
                  <Text style={styles.overlayText}>❤️ LIKE</Text>
                </Animated.View>

                {/* Dislike overlay */}
                <Animated.View style={[styles.overlay, styles.dislikeOverlay, dislikeOverlayStyle]}>
                  <Text style={styles.overlayText}>❌ PASS</Text>
                </Animated.View>

                <Text style={styles.songTitle}>{currentSong.title}</Text>
                <Text style={styles.artistName}>{currentSong.artists}</Text>
                <View style={styles.tagsContainer}>
                  {currentSong.tags.slice(0, 3).map((tag, index) => (
                    <View key={index} style={styles.tag}>
                      <Text style={styles.tagText}>{tag}</Text>
                    </View>
                  ))}
                </View>
              </Animated.View>
            </GestureDetector>
          </View>

          {/* Manual buttons */}
          <View style={styles.buttonContainer}>
            <TouchableOpacity 
              style={[styles.swipeButton, styles.dislikeButton]} 
              onPress={() => handleSwipe(false)}
              disabled={isLoading}
            >
              <Text style={styles.buttonText}>❌</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.swipeButton, styles.likeButton]} 
              onPress={() => handleSwipe(true)}
              disabled={isLoading}
            >
              <Text style={styles.buttonText}>❤️</Text>
            </TouchableOpacity>
          </View>

          {isLoading && (
            <Text style={styles.loadingText}>次の楽曲を取得中...</Text>
          )}
        </View>
      </ImageBackground>
    </GestureHandlerRootView>
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
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 38,
    color: "#fff",
    marginBottom: 20,
    fontWeight: "bold",
    textAlign: "center",
  },
  likeCounter: {
    fontSize: 18,
    color: "#fff",
    marginBottom: 20,
    fontWeight: "bold",
    textAlign: "center",
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    paddingHorizontal: 15,
    paddingVertical: 5,
    borderRadius: 15,
  },
  cardContainer: {
    width: screenWidth * 0.85,
    height: screenHeight * 0.6,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 40,
  },
  musicCard: {
    position: 'absolute',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 20,
    padding: 30,
    width: '100%',
    height: '80%',
    alignItems: 'center',
    justifyContent: 'center',
    borderColor: 'white',
    borderWidth: 3,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 10,
    },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  nextCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    transform: [{ scale: 0.95 }],
    zIndex: 0,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  likeOverlay: {
    backgroundColor: 'rgba(76, 175, 80, 0.8)',
  },
  dislikeOverlay: {
    backgroundColor: 'rgba(244, 67, 54, 0.8)',
  },
  overlayText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 4,
  },
  songTitle: {
    fontSize: 28,
    color: '#333',
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 15,
  },
  artistName: {
    fontSize: 20,
    color: '#666',
    textAlign: 'center',
    marginBottom: 25,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  tag: {
    backgroundColor: '#2C7FD5',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    margin: 5,
  },
  tagText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '60%',
  },
  swipeButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'white',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 5,
    },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 5,
  },
  likeButton: {
    backgroundColor: '#4CAF50',
  },
  dislikeButton: {
    backgroundColor: '#F44336',
  },
  buttonText: {
    fontSize: 24,
  },
  loadingText: {
    color: 'white',
    fontSize: 16,
    marginTop: 20,
    textAlign: 'center',
  },
});