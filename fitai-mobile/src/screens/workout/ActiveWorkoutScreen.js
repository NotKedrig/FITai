import React, { useContext, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Swipeable } from 'react-native-gesture-handler';
import { WorkoutContext } from '../../context/WorkoutContext';
import { AuthContext } from '../../context/AuthContext';
import * as workoutsApi from '../../api/workouts';

export default function ActiveWorkoutScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { token } = useContext(AuthContext);
  const {
    workout,
    exercises,
    latestRecommendation,
    isLogging,
    initWorkout,
    logSet,
    removeSet,
    clearWorkout,
  } = useContext(WorkoutContext);

  const routeWorkout = route.params && route.params.workout ? route.params.workout : null;

  const [isEnding, setIsEnding] = useState(false);
  const [endError, setEndError] = useState(null);
  const [removeError, setRemoveError] = useState(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [inputState, setInputState] = useState({});

  useEffect(() => {
    if (routeWorkout && (!workout || workout.id !== routeWorkout.id)) {
      initWorkout(routeWorkout);
    }
  }, [routeWorkout, workout, initWorkout]);

  useEffect(() => {
    const startedAtString =
      (workout && workout.started_at) || (routeWorkout && routeWorkout.started_at);
    if (!startedAtString) {
      return undefined;
    }
    const startedAt = new Date(startedAtString);

    const updateElapsed = () => {
      const now = new Date();
      const diffSeconds = Math.max(0, Math.floor((now.getTime() - startedAt.getTime()) / 1000));
      setElapsedSeconds(diffSeconds);
    };

    updateElapsed();
    const intervalId = setInterval(updateElapsed, 1000);
    return () => clearInterval(intervalId);
  }, [workout, routeWorkout]);

  useEffect(() => {
    setInputState((current) => {
      const next = { ...current };
      exercises.forEach((block) => {
        const id = block.exercise && block.exercise.id;
        if (!id) return;
        if (!next[id]) {
          next[id] = {
            weight:
              latestRecommendation && latestRecommendation.suggested_weight_kg != null
                ? String(latestRecommendation.suggested_weight_kg)
                : '',
            reps:
              latestRecommendation && latestRecommendation.suggested_reps != null
                ? String(latestRecommendation.suggested_reps)
                : '',
            rpe: '',
            isWarmup: false,
          };
        }
      });
      return next;
    });
  }, [exercises, latestRecommendation]);

  const formattedTimer = useMemo(() => {
    const minutes = Math.floor(elapsedSeconds / 60);
    const seconds = elapsedSeconds % 60;
    const m = String(minutes).padStart(2, '0');
    const s = String(seconds).padStart(2, '0');
    return `${m}:${s}`;
  }, [elapsedSeconds]);

  const handleEndWorkout = async () => {
    const currentWorkout = workout || routeWorkout;
    if (!currentWorkout || !currentWorkout.id) {
      setEndError('Workout not found.');
      return;
    }
    if (!token) {
      setEndError('You are not authenticated.');
      return;
    }

    setIsEnding(true);
    setEndError(null);
    try {
      await workoutsApi.endWorkout(token, currentWorkout.id);
      clearWorkout();
      navigation.reset({
        index: 0,
        routes: [{ name: 'HomeMain' }],
      });
    } catch (err) {
      setEndError(err.message || 'Failed to end workout.');
    } finally {
      setIsEnding(false);
    }
  };

  const handleAddExercise = () => {
    navigation.navigate('ExercisePicker');
  };

  const handleRemoveSet = async (setId) => {
    try {
      setRemoveError(null);
      await removeSet(setId);
    } catch (error) {
      setRemoveError(error.message || 'Failed to delete set.');
    }
  };
  const handleChangeInput = (exerciseId, field, value) => {
    setInputState((current) => ({
      ...current,
      [exerciseId]: {
        ...(current[exerciseId] || {}),
        [field]: value,
      },
    }));
  };

  const handleToggleWarmup = (exerciseId) => {
    setInputState((current) => {
      const prev = current[exerciseId] || {
        weight: '',
        reps: '',
        rpe: '',
        isWarmup: false,
      };
      const nextIsWarmup = !prev.isWarmup;
      return {
        ...current,
        [exerciseId]: {
          weight: nextIsWarmup ? '' : prev.weight,
          reps: nextIsWarmup ? '' : prev.reps,
          rpe: nextIsWarmup ? '' : prev.rpe,
          isWarmup: nextIsWarmup,
        },
      };
    });
  };

  const handleCompleteSet = async (exerciseId) => {
    const state = inputState[exerciseId] || {};
    const rawWeight = state.weight || '';
    const rawReps = state.reps || '';
    const rawRpe = state.rpe || '';
    const isWarmup = !!state.isWarmup;

    if (!rawWeight.trim() || !rawReps.trim()) {
      setRemoveError('Weight and reps are required.');
      return;
    }

    const weight = parseFloat(rawWeight.replace(',', '.'));
    const reps = parseInt(rawReps, 10);
    if (Number.isNaN(weight) || Number.isNaN(reps)) {
      setRemoveError('Weight and reps must be numbers.');
      return;
    }

    let rpe = null;
    if (rawRpe.trim()) {
      const parsedRpe = parseFloat(rawRpe.replace(',', '.'));
      if (Number.isNaN(parsedRpe)) {
        setRemoveError('RPE must be a number.');
        return;
      }
      rpe = parsedRpe;
    }

    setRemoveError(null);
    try {
      await logSet(exerciseId, weight, reps, rpe, isWarmup);
      setInputState((current) => ({
        ...current,
        [exerciseId]: {
          weight:
            !isWarmup &&
            latestRecommendation &&
            latestRecommendation.suggested_weight_kg != null
              ? String(latestRecommendation.suggested_weight_kg)
              : '',
          reps:
            !isWarmup &&
            latestRecommendation &&
            latestRecommendation.suggested_reps != null
              ? String(latestRecommendation.suggested_reps)
              : '',
          rpe: '',
          isWarmup: false,
        },
      }));
    } catch (error) {
      setRemoveError(error.message || 'Failed to log set.');
    }
  };

  const renderExerciseBlock = ({ item }) => {
    const block = item;
    const exercise = block.exercise || {};
    const exerciseId = exercise.id;
    const completedSets = block.sets || [];
    const state = (exerciseId && inputState[exerciseId]) || {
      weight: '',
      reps: '',
      rpe: '',
      isWarmup: false,
    };
    const nextSetNumber = completedSets.length + 1;

    const renderCompletedSet = (entry) => {
      const set = entry.set;
      const rightActions = () => (
        <TouchableOpacity
          style={styles.deleteAction}
          activeOpacity={0.8}
          onPress={() => handleRemoveSet(set.id)}
        >
          <Text style={styles.deleteActionText}>Delete</Text>
        </TouchableOpacity>
      );

      return (
        <Swipeable key={set.id} renderRightActions={rightActions}>
          <View
            style={[
              styles.completedRow,
              set.is_warmup && styles.warmupRow,
            ]}
          >
            <Text
              style={[
                styles.completedText,
                set.is_warmup && styles.warmupText,
              ]}
            >
              {`Set ${set.set_number} | ${set.weight_kg}kg x ${set.reps}${
                set.rpe != null ? ` | RPE ${set.rpe}` : ''
              }`}
            </Text>
            {set.is_warmup && (
              <View style={styles.warmupBadge}>
                <Text style={styles.warmupBadgeText}>W</Text>
              </View>
            )}
          </View>
        </Swipeable>
      );
    };

    return (
      <View style={styles.exerciseCard}>
        <Text style={styles.exerciseName}>
          {exercise.name || 'Exercise'}
        </Text>
        <Text style={styles.exerciseMeta}>
          {(exercise.muscle_group || '').toString()}
        </Text>

        <View style={styles.setsContainer}>
          {completedSets.map(renderCompletedSet)}

          {exerciseId && (
            <View style={styles.activeSetRow}>
              <Text style={styles.activeSetNumber}>#{nextSetNumber}</Text>
              <TextInput
                style={styles.activeInput}
                placeholder="kg"
                placeholderTextColor="#666666"
                keyboardType="numeric"
                value={state.weight}
                onChangeText={(text) =>
                  handleChangeInput(exerciseId, 'weight', text)
                }
              />
              <TextInput
                style={styles.activeInput}
                placeholder="Reps"
                placeholderTextColor="#666666"
                keyboardType="numeric"
                value={state.reps}
                onChangeText={(text) =>
                  handleChangeInput(exerciseId, 'reps', text)
                }
              />
              <TextInput
                style={styles.activeInput}
                placeholder="RPE"
                placeholderTextColor="#666666"
                keyboardType="numeric"
                value={state.rpe}
                onChangeText={(text) =>
                  handleChangeInput(exerciseId, 'rpe', text)
                }
              />
              <TouchableOpacity
                style={[
                  styles.warmupToggle,
                  state.isWarmup && styles.warmupToggleActive,
                ]}
                onPress={() => handleToggleWarmup(exerciseId)}
              >
                <Text style={styles.warmupToggleText}>W</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.completeButton,
                  (isLogging || !state.weight || !state.reps) &&
                    styles.completeButtonDisabled,
                ]}
                activeOpacity={0.9}
                onPress={() => handleCompleteSet(exerciseId)}
                disabled={isLogging || !state.weight || !state.reps}
              >
                {isLogging ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <Text style={styles.completeButtonText}>✓</Text>
                )}
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
          <Text style={styles.headerTitle}>
            {(workout && workout.name) || (routeWorkout && routeWorkout.name) || 'Workout'}
          </Text>
          <Text style={styles.headerTimer}>{formattedTimer}</Text>
        </View>

        <View style={styles.content}>
          {latestRecommendation && (
            <View style={styles.recommendationCard}>
              <Text style={styles.recommendationTitle}>Latest recommendation</Text>
              <Text style={styles.recommendationMain}>
                Next set:{' '}
                {latestRecommendation.suggested_weight_kg}kg x{' '}
                {latestRecommendation.suggested_reps}
              </Text>
              {latestRecommendation.explanation ? (
                <Text style={styles.recommendationExplanation}>
                  {latestRecommendation.explanation}
                </Text>
              ) : null}
              <View style={styles.recommendationMetaRow}>
                {latestRecommendation.model_used ? (
                  <View style={styles.modelBadge}>
                    <Text style={styles.modelBadgeText}>
                      {latestRecommendation.model_used}
                    </Text>
                  </View>
                ) : null}
                {latestRecommendation.latency_ms != null ? (
                  <Text style={styles.latencyText}>
                    {latestRecommendation.latency_ms} ms
                  </Text>
                ) : null}
              </View>
            </View>
          )}

          {removeError ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{removeError}</Text>
            </View>
          ) : null}

          <FlatList
            data={exercises}
            keyExtractor={(item) =>
              String(item.exercise && item.exercise.id
                ? item.exercise.id
                : Math.random())
            }
            renderItem={renderExerciseBlock}
            contentContainerStyle={styles.listContent}
          />
        </View>

        {endError ? (
          <View style={styles.footerErrorContainer}>
            <Text style={styles.errorText}>{endError}</Text>
          </View>
        ) : null}

        <View style={[styles.footer, { paddingBottom: insets.bottom + 12 }]}>
          <TouchableOpacity
            style={styles.addExerciseButton}
            activeOpacity={0.9}
            onPress={handleAddExercise}
          >
            <Text style={styles.addExerciseButtonText}>Add Exercise</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.endButton, isEnding && styles.endButtonDisabled]}
            activeOpacity={0.9}
            onPress={handleEndWorkout}
            disabled={isEnding}
          >
            {isEnding ? (
              <ActivityIndicator size="small" color="#ffffff" />
            ) : (
              <Text style={styles.endButtonText}>End Workout</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
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
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  headerTimer: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6C63FF',
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  recommendationCard: {
    backgroundColor: '#151530',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  recommendationTitle: {
    fontSize: 13,
    color: '#bbbbff',
    marginBottom: 4,
  },
  recommendationMain: {
    fontSize: 15,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  recommendationExplanation: {
    fontSize: 13,
    color: '#ddddff',
    marginBottom: 8,
  },
  recommendationMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  modelBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: '#26264d',
  },
  modelBadgeText: {
    fontSize: 11,
    color: '#ffffff',
  },
  latencyText: {
    fontSize: 11,
    color: '#bbbbbb',
  },
  listContent: {
    paddingBottom: 16,
  },
  exerciseCard: {
    backgroundColor: '#1C1C1E',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
  },
  exerciseName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  exerciseMeta: {
    marginTop: 4,
    fontSize: 13,
    color: '#888888',
  },
  setsContainer: {
    marginTop: 12,
  },
  completedRow: {
    backgroundColor: '#2A2A2A',
    padding: 12,
    borderRadius: 10,
    marginVertical: 4,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  completedText: {
    color: '#FFFFFF',
    fontSize: 14,
  },
  warmupRow: {
    backgroundColor: '#232323',
  },
  warmupText: {
    color: '#AAAAAA',
  },
  warmupBadge: {
    backgroundColor: '#FFD60A',
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  warmupBadgeText: {
    color: '#000',
    fontSize: 12,
    fontWeight: '700',
  },
  activeSetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  activeSetNumber: {
    fontSize: 13,
    color: '#ffffff',
    marginRight: 8,
  },
  activeInput: {
    flex: 1,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333333',
    paddingHorizontal: 8,
    paddingVertical: 6,
    color: '#ffffff',
    backgroundColor: '#111111',
    fontSize: 13,
    marginHorizontal: 4,
    textAlign: 'center',
  },
  warmupToggle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#555555',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 4,
  },
  warmupToggleActive: {
    backgroundColor: '#444444',
    borderColor: '#ffffff',
  },
  warmupToggleText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  completeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 4,
    backgroundColor: '#4CAF50',
  },
  completeButtonDisabled: {
    backgroundColor: '#333333',
  },
  completeButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  deleteAction: {
    backgroundColor: '#FF4B4B',
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingHorizontal: 20,
    marginVertical: 2,
    borderRadius: 10,
  },
  deleteActionText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  errorContainer: {
    marginBottom: 8,
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#331111',
  },
  errorText: {
    color: '#ff9999',
    fontSize: 13,
  },
  footerErrorContainer: {
    paddingHorizontal: 16,
    paddingTop: 4,
  },
  footer: {
    paddingHorizontal: 16,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#111111',
  },
  addExerciseButton: {
    backgroundColor: '#2C2C2E',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#3A3A3C',
    shadowColor: '#000000',
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 3,
    elevation: 2,
  },
  addExerciseButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  endButton: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#3A3A3C',
  },
  endButtonDisabled: {
    opacity: 0.7,
  },
  endButtonText: {
    color: '#FF4D4D',
    fontSize: 16,
    fontWeight: '700',
  },
});


