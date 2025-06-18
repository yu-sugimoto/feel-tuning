import { View, Text, StyleSheet, Dimensions, TouchableOpacity, ImageBackground } from "react-native";
import { useRouter } from "expo-router";

const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;

export default function Index() {
  const router = useRouter();

  return (
    <ImageBackground
      source={require("../assets/images/background.png")}
      style={styles.background}
      resizeMode="cover"
    >
      <View style={styles.overlay}>
        <Text style={styles.title}>「この写真にこの曲！」{"\n"}              を誰でも簡単に。</Text>
        <TouchableOpacity style={styles.button} onPress={() => router.push({ pathname: "/login" })}>
          <Text style={styles.buttonText}>ログイン</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.button} onPress={() => router.push({ pathname: "/signup" })}>
          <Text style={styles.buttonText}>アカウント作成</Text>
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
  overlay: {
    position: "absolute",
    bottom: 100,
    alignItems: "center",
  },
  title: {
    fontSize: 38,
    color: "#fff",
    marginBottom: 40,
    fontWeight: "bold",
    textAlign: "center",
    bottom: 230,
  },
  button: {
    backgroundColor: "#2C7FD5",
    padding: 16,
    borderColor: "white",
    borderWidth: 4,
    borderRadius: 10,
    marginTop: 20,
    minWidth: 330,
    alignItems: "center",
  },
  buttonText: {
    color: "white",
    fontSize: 35,
    fontWeight: "bold",
  },
});
