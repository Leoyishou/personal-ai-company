import React, { useEffect, useState } from 'react';
import { Button, SafeAreaView, StyleSheet, Text, View, NativeModules } from 'react-native';

const { AudioController } = NativeModules;

export default function App() {
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const p = await AudioController.isPlaying();
        setPlaying(!!p);
      } catch {}
    })();
  }, []);

  const onToggle = async () => {
    try {
      await AudioController.toggle();
      const p = await AudioController.isPlaying();
      setPlaying(!!p);
    } catch (e) {
      // no-op
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Dejavu Hybrid – RN</Text>
        <Button title={playing ? 'Pause (Native)' : 'Play (Native)'} onPress={onToggle} />
        <Text style={styles.status}>Status: {playing ? 'Playing' : 'Paused'}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  content: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 24 },
  title: { fontSize: 28, fontWeight: '700' },
  status: { color: '#666' }
});

