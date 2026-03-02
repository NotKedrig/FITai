import React, { useContext, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  StyleSheet,
  Text,
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
  const { workout, sets, initWorkout, removeSet, clearWorkout } = useContext(WorkoutContext);

  const routeWorkout = route.params && route.params.workout ? route.params.workout : null;

  const [isEnding, setIsEnding] = useState(false);
  const [endError, setEndError] = useState(null);
  const [removeError, setRemoveError] = useState(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (routeWorkout) {
      initWorkout(routeWorkout);
    }
  }, [routeWorkout, initWorkout]);

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

  const latestRecommendation = useMemo(() => {
    if (!sets || sets.length === 0) return null;
    const last = sets[sets.length - 1];
    return last.recommendation || null;
  }, [sets]);

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

  const renderSetItem = ({ item }) => {
    const set = item.set;
    const exerciseName = set.exercise_name || item.exercise_name || 'Exercise';
    const labelParts = [];
    if (set.is_warmup) {
      labelParts.push('Warmup');
    } else {
      labelParts.push(`${set.weight_kg}kg x ${set.reps}`);
      if (set.rpe != null) {
        labelParts.push(`@ RPE ${set.rpe}`);
      }
    }
    const label = labelParts.join(' ');

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
      <Swipeable renderRightActions={rightActions}>
        <View style={styles.setItem}>
          <View style={styles.setItemHeader}>
            <Text style={styles.setNumber}>Set {set.set_number}</Text>
            <Text style={styles.setExerciseName}>{exerciseName}</Text>
          </View>
          <Text style={styles.setDetails}>{label}</Text>
        </View>
      </Swipeable>
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
            data={sets}
            keyExtractor={(item) => String(item.set.id)}
            renderItem={renderSetItem}
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
  setItem: {
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    padding: 12,
    marginBottom: 10,
  },
  setItemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  setNumber: {
    fontSize: 13,
    fontWeight: '600',
    color: '#cccccc',
  },
  setExerciseName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  setDetails: {
    fontSize: 13,
    color: '#dddddd',
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
    backgroundColor: '#6C63FF',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 8,
  },
  addExerciseButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  endButton: {
    backgroundColor: '#FF4B4B',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  endButtonDisabled: {
    opacity: 0.7,
  },
  endButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
});


