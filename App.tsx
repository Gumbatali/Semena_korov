import React, { useState, useEffect, useCallback } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  ActivityIndicator,
  NativeModules,
} from 'react-native';
import { launchImageLibrary, ImagePickerResponse, ImageLibraryOptions, PhotoQuality } from 'react-native-image-picker';
import RNFS from 'react-native-fs';
import CustomButton from './src/components/CustomButton';

const { ExecuTorchModule } = NativeModules;

const App = () => {
  const [fileName, setFileName] = useState<string | null>(null);
  const [message, setMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [phase, setPhase] = useState<string | null>(null);
  const [phases, setPhases] = useState<string[]>([]);

  // Пути к активам
  const modelPath = `${RNFS.DocumentDirectoryPath}/mobilenet_phases.pt`;
  const phasesPath = `${RNFS.DocumentDirectoryPath}/phases.txt`;

  const copyAssetsIfNeeded = useCallback(async () => {
    try {
      console.log('Checking assets...');
      console.log('Model path:', modelPath);
      console.log('Phases path:', phasesPath);
      const modelExists = await RNFS.exists(modelPath);
      console.log('Model exists in DocumentDirectory:', modelExists);
      if (!modelExists) {
        const assetModelPath = 'mobilenet_phases.pt';
        console.log('Copying model from assets:', assetModelPath);
        try {
          await RNFS.copyFileAssets(assetModelPath, modelPath);
          console.log('Model copied successfully');
        } catch (copyError) {
          console.error('Failed to copy model:', copyError);
          throw new Error(`Failed to copy model: ${JSON.stringify(copyError)}`);
        }
      }
      const phasesExists = await RNFS.exists(phasesPath);
      console.log('Phases exists in DocumentDirectory:', phasesExists);
      if (!phasesExists) {
        const assetPhasesPath = 'phases.txt';
        console.log('Copying phases from assets:', assetPhasesPath);
        try {
          await RNFS.copyFileAssets(assetPhasesPath, phasesPath);
          console.log('Phases copied successfully');
        } catch (copyError) {
          console.error('Failed to copy phases:', copyError);
          throw new Error(`Failed to copy phases: ${JSON.stringify(copyError)}`);
        }
      }
      // Загружаем фазы
      const phasesContent = await RNFS.readFile(phasesPath, 'utf8');
      const phasesArray = phasesContent.split('\n').map((p) => p.trim()).filter((p) => p);
      setPhases(phasesArray);
      setMessage('✅ Модель готова к работе');
    } catch (error: any) {
      console.error('Error copying assets:', error);
      setMessage(`❌ Ошибка загрузки модели: ${error.message}`);
    }
  }, [modelPath, phasesPath]);

  const pickFile = async () => {
    try {
      setMessage('');
      setFileName(null);
      setPhase(null);
      setLoading(true);

      const options: ImageLibraryOptions = {
        mediaType: 'photo',
        quality: 1 as PhotoQuality,
      };
      const result: ImagePickerResponse = await new Promise((resolve, reject) => {
        launchImageLibrary(options, (response) => {
          if (response.errorCode) {
            reject(new Error(response.errorMessage));
          } else {
            resolve(response);
          }
        });
      });

      if (result.didCancel) {
        setMessage('Загрузка отменена');
        setLoading(false);
        return;
      }

      if (result.errorCode) {
        setMessage(`❌ Ошибка: ${result.errorMessage}`);
        setLoading(false);
        return;
      }

      const asset = result.assets && result.assets[0];
      if (!asset) {
        setMessage('❌ Нет файла');
        setLoading(false);
        return;
      }

      const { fileName: name, uri, fileSize, type: mimeType } = asset;
      const safeName = name ? name.replace(/\s+/g, '_') : 'image.jpg';

      const allowedFormats = ['image/jpeg', 'image/png'];
      const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

      if (mimeType && !allowedFormats.includes(mimeType)) {
        setMessage('❌ Формат должен быть JPEG или PNG');
        setLoading(false);
        return;
      }

      if (fileSize && fileSize > MAX_FILE_SIZE) {
        setMessage('❌ Файл слишком большой (макс. 10 МБ)');
        setLoading(false);
        return;
      }

      setFileName(safeName);
      setMessage(`✅ Файл загружен: ${safeName}`);

      if (uri) {
        const localUri = `${RNFS.DocumentDirectoryPath}/${safeName}`;
        await RNFS.copyFile(uri, localUri);

        // Инференс модели
        if (phases.length > 0) {
          try {
            // Загрузка модели
            await ExecuTorchModule.loadModel(modelPath);
            // Предобработка изображения
            const inputs = { uri: localUri, size: 224 };
            const outputs = await ExecuTorchModule.run(inputs);
            const scores = outputs[0];
            const maxIdx = scores.indexOf(Math.max(...scores));
            const predictedPhase = phases[maxIdx] || 'Неизвестная фаза';
            setPhase(predictedPhase);
            setMessage(`✅ Фаза: ${predictedPhase}`);
          } catch (error: any) {
            console.error('Error in inference:', error);
            setMessage(`❌ Ошибка анализа: ${error.message}`);
          }
        } else {
          setMessage('❌ Модель не готова');
        }
      }
    } catch (error: any) {
      console.error('Error in pickFile:', error);
      setMessage(`❌ Ошибка: ${error.message || 'Неизвестная ошибка'}`);
    } finally {
      setLoading(false);
    }
  };

  const getMessageStyle = () => {
    if (message.includes('✅')) return { color: '#4CAF50', fontWeight: '600' as const };
    if (message.includes('❌')) return { color: '#F44336', fontWeight: '600' as const };
    return { color: '#FF9800', fontWeight: '600' as const };
  };

  useEffect(() => {
    copyAssetsIfNeeded();
  }, [copyAssetsIfNeeded]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#000000" />
      <ScrollView contentInsetAdjustmentBehavior="automatic" style={styles.scrollView}>
        <View style={styles.body}>
          <Text style={styles.title}>Ekoniva CV Detector</Text>
          <CustomButton
            title={loading ? 'Обработка...' : 'Выбрать фото'}
            onPress={pickFile}
            disabled={loading}
          />
          {fileName && (
            <View style={styles.fileContainer}>
              <Text style={styles.fileName}>Файл: {fileName}</Text>
            </View>
          )}
          {phase && (
            <View style={styles.phaseContainer}>
              <Text style={styles.phaseText}>Фаза: {phase}</Text>
            </View>
          )}
          {message && (
            <View style={styles.messageContainer}>
              {loading ? (
                <View style={styles.progressContainer}>
                  <ActivityIndicator size="small" color="#4CAF50" />
                  <Text style={[styles.message, { color: '#4CAF50' }]}>Обработка...</Text>
                </View>
              ) : (
                <Text style={[styles.message, getMessageStyle()]}>{message}</Text>
              )}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  scrollView: {
    flex: 1,
  },
  body: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: 'white',
    marginBottom: 30,
    textAlign: 'center',
  },
  fileContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#1A1A1A',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  phaseContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#1A1A1A',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  fileName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#4CAF50',
  },
  phaseText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#4CAF50',
  },
  messageContainer: {
    marginTop: 20,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#1A1A1A',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
  },
  message: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});

export default App;