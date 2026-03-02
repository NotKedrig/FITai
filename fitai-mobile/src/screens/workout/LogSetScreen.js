import React, { useContext, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { WorkoutContext } from '../../context/WorkoutContext';

export default function LogSetScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const insets = useSafeAreaInsets();
  const { logSet, isLogging, logSetError } = useContext(WorkoutContext);

  const exercise = route.params && route.params.exercise ? route.params.exercise : null;

  const [isWarmup, setIsWarmup] = useState(false);
  const [weight, setWeight] = useState('');
  const [reps, setReps] = useState('');
  const [rpe, setRpe] = useState('');
  const [localError, setLocalError] = useState(null);

  const handleSubmit = async () => {
    if (!exercise || !exercise.id) {
      setLocalError('Exercise not found.');
      return;
    }
    if (!weight.trim() || !reps.trim()) {
      setLocalError('Weight and reps are required.');
      return;
    }
    const weightValue = parseFloat(weight.replace(',', '.'));
    const repsValue = parseInt(reps, 10);
    if (Number.isNaN(weightValue) || Number.isNaN(repsValue)) {
      setLocalError('Weight and reps must be numbers.');
      return;
    }

    let rpeValue = null;
    if (rpe.trim()) {
      const parsedRpe = parseFloat(rpe.replace(',', '.'));
      if (Number.isNaN(parsedRpe)) {
        setLocalError('RPE must be a number between 1 and 10.');
        return;
      }
      rpeValue = parsedRpe;
    }

    setLocalError(null);
    try {
      await logSet(exercise.id, weightValue, repsValue, rpeValue, isWarmup);
      navigation.goBack();
    } catch (error) {
      // logSetError from context will handle messaging; keep local error as generic.
    }
  };

  const effectiveError = localError || logSetError;

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>‹</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>
            {exercise && exercise.name ? exercise.name : 'Log Set'}
          </Text>
          <View style={styles.headerRightPlaceholder} />
        </View>

        <ScrollView
          style={styles.content}
          contentContainerStyle={styles.contentContainer}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.row}>
            <Text style={styles.label}>Warmup set</Text>
            <Switch
              value={isWarmup}
              onValueChange={setIsWarmup}
              thumbColor={isWarmup ? '#ffffff' : '#888888'}
              trackColor={{ false: '#444444', true: '#6C63FF' }}
            />
          </View>

          <Text style={styles.label}>Weight (kg)</Text>
          <TextInput
            style={styles.input}
            placeholder="Weight (kg)"
            placeholderTextColor="#666666"
            value={weight}
            onChangeText={setWeight}
            keyboardType="numeric"
            returnKeyType="next"
          />

          <Text style={styles.label}>Reps</Text>
          <TextInput
            style={styles.input}
            placeholder="Reps"
            placeholderTextColor="#666666"
            value={reps}
            onChangeText={setReps}
            keyboardType="numeric"
            returnKeyType="next"
          />

          <Text style={styles.label}>RPE (optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="RPE (1-10)"
            placeholderTextColor="#666666"
            value={rpe}
            onChangeText={setRpe}
            keyboardType="numeric"
            returnKeyType="done"
          />

          {effectiveError ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{effectiveError}</Text>
            </View>
          ) : null}
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.primaryButton, isLogging && styles.primaryButtonDisabled]}
            activeOpacity={0.9}
            onPress={handleSubmit}
            disabled={isLogging}
          >
            {isLogging ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <Text style={styles.primaryButtonText}>Log Set</Text>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  backButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333333',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButtonText: {
    color: '#ffffff',
    fontSize: 18,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  headerRightPlaceholder: {
    width: 32,
    height: 32,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
  },
  contentContainer: {
    paddingBottom: 24,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 16,
    marginBottom: 8,
  },
  label: {
    marginTop: 16,
    marginBottom: 8,
    fontSize: 14,
    color: '#cccccc',
  },
  input: {
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#333333',
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    backgroundColor: '#111111',
    fontSize: 15,
  },
  errorContainer: {
    marginTop: 12,
    padding: 10,
    borderRadius: 8,
    backgroundColor: '#331111',
  },
  errorText: {
    color: '#ff9999',
    fontSize: 13,
  },
  footer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#111111',
  },
  primaryButton: {
    backgroundColor: '#6C63FF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  primaryButtonDisabled: {
    opacity: 0.7,
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
});

