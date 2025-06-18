import { View, Text, StyleSheet, ImageBackground, Dimensions, TouchableOpacity, Image } from 'react-native';
import { useRouter } from 'expo-router';

const screenHeight = Dimensions.get("window").height;
const screenWidth = Dimensions.get("window").width;

export default function AnalysisScreen() {
  const router = useRouter();

  return (
    <ImageBackground
      source={require('../assets/images/background.png')}
      style={styles.background}
      resizeMode="cover"
    >
      <View style={styles.container}>
        <Text style={styles.title}>分析データはまだありません</Text>

        <View style={styles.navbar}>
          <TouchableOpacity style={styles.navItem} onPress={() => router.push('/photo')}>
            <Image source={require("../assets/images/camera.png")} style={styles.icon} />
            <Text style={styles.navText}>カメラ</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.navItem} onPress={() => router.push('/history')}>
            <Image source={require("../assets/images/history.png")} style={styles.icon} />
            <Text style={styles.navText}>履歴</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.navItem, styles.activeNavItem]}>
            <Image source={require("../assets/images/analysis.png")} style={styles.icon} />
            <Text style={styles.activeNavText}>分析</Text>
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
    justifyContent: 'center',
    alignItems: 'center',
    paddingBottom: 80,
  },
  title: {
    fontSize: 24,
    color: '#fff',
    fontWeight: 'bold',
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
