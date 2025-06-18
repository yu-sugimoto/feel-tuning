import { useEffect, useRef, useState } from "react";
import { View, Image, StyleSheet, Dimensions, Animated } from "react-native";
import { Stack } from "expo-router";

const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;

export default function RootLayout() {
  const [showSplash, setShowSplash] = useState(true);
  const fadeAnim = useRef(new Animated.Value(1)).current; // アニメーション用の透明度

  useEffect(() => {
    const timer = setTimeout(() => {
      // フェードアウト
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 1000,
        useNativeDriver: true,
      }).start(() => {
        // アニメーション後にスプラッシュ非表示
        setShowSplash(false);
      });
    }, 2000); // フェードアウト開始を少し遅らせる

    return () => clearTimeout(timer);
  }, []);

  if (showSplash) {
    return (
      <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
        <Image
          source={require("../assets/images/splash.png")}
          style={styles.image}
          resizeMode="cover"
        />
      </Animated.View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
      }}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    width: screenWidth,
    height: screenHeight,
    justifyContent: "center",
    alignItems: "center",
  },
  image: {
    width: screenWidth,
    height: screenHeight,
  },
});