import React, { useCallback, useContext, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { AuthContext } from '../../context/AuthContext';
import * as workoutsApi from '../../api/workouts';

function formatGreetingName(user) {
  if (user && user.username) {
    return user.username;
  }
  if (user && user.email) {
    return user.email;
  }
  return 'Athlete';
}

function getTimeOfDayGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

function formatWorkoutDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const formatter = new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
  return formatter.format(date);
}

function formatDuration(startedAt, endedAt) {
  if (!startedAt) return '';
  if (!endedAt) return 'In progress';
  const start = new Date(startedAt);
  const end = new Date(endedAt);
  const diffMs = end.getTime() - start.getTime();
  if (diffMs <= 0) return 'In progress';
  const totalMinutes = Math.round(diffMs / 60000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

export default function HomeScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { token, user, logout } = useContext(AuthContext);
  const [workouts, setWorkouts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const loadWorkouts = useCallback(
    async (options = { refreshing: false }) => {
      if (!token) {
        return;
      }
      if (options.refreshing) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }
      setError(null);
      try {
        const data = await workoutsApi.getWorkouts(token);
        const list = Array.isArray(data) ? data : data?.items || [];
        const sorted = list
          .slice()
          .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
        setWorkouts(sorted.slice(0, 5));
      } catch (err) {
        setError(err.message || 'Failed to load workouts.');
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [token]
  );

  useEffect(() => {
    loadWorkouts();
  }, [loadWorkouts]);

  const onRefresh = useCallback(() => {
    loadWorkouts({ refreshing: true });
  }, [loadWorkouts]);

  const renderWorkoutItem = ({ item }) => {
    return (
      <TouchableOpacity style={styles.workoutCard} activeOpacity={0.8}>
        <View style={styles.workoutCardHeader}>
          <Text style={styles.workoutName}>{item.name}</Text>
          <Text style={styles.workoutDate}>{formatWorkoutDate(item.started_at)}</Text>
        </View>
        <Text style={styles.workoutDuration}>
          {formatDuration(item.started_at, item.ended_at)}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <Text style={styles.headerTitle}>FitAI</Text>
        <TouchableOpacity
          onPress={logout}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          style={styles.logoutIconButton}
        >
          <Text style={styles.logoutIconText}>⎋</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        <View style={styles.greetingContainer}>
          <Text style={styles.greetingText}>
            {getTimeOfDayGreeting()},{' '}
            <Text style={styles.greetingName}>{formatGreetingName(user)}</Text>
          </Text>
          <Text style={styles.greetingSubtitle}>Ready to train today?</Text>
        </View>

        <TouchableOpacity
          style={styles.primaryButton}
          activeOpacity={0.9}
          onPress={() => navigation.navigate('StartWorkout')}
        >
          <Text style={styles.primaryButtonText}>Start Workout</Text>
        </TouchableOpacity>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Workouts</Text>
          {isLoading && !isRefreshing && (
            <ActivityIndicator size="small" color="#6C63FF" style={styles.sectionSpinner} />
          )}
        </View>

        {error && !isLoading && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={() => loadWorkouts()}>
              <Text style={styles.retryButtonText}>Retry</Text>
            </TouchableOpacity>
          </View>
        )}

        {!error && !isLoading && workouts.length === 0 && (
          <View style={styles.emptyStateContainer}>
            <Text style={styles.emptyStateText}>
              No workouts yet. Start your first one!
            </Text>
          </View>
        )}

        <FlatList
          data={workouts}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderWorkoutItem}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              tintColor="#6C63FF"
              colors={['#6C63FF']}
              refreshing={isRefreshing}
              onRefresh={onRefresh}
            />
          }
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#ffffff',
  },
  logoutIconButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#333333',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoutIconText: {
    color: '#ffffff',
    fontSize: 18,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 16,
  },
  greetingContainer: {
    marginTop: 16,
    marginBottom: 24,
  },
  greetingText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ffffff',
  },
  greetingName: {
    color: '#6C63FF',
  },
  greetingSubtitle: {
    marginTop: 6,
    fontSize: 14,
    color: '#cccccc',
  },
  primaryButton: {
    backgroundColor: '#6C63FF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 24,
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  sectionSpinner: {
    marginLeft: 8,
  },
  listContent: {
    paddingBottom: 80,
  },
  workoutCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  workoutCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  workoutName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  workoutDate: {
    fontSize: 13,
    color: '#bbbbbb',
  },
  workoutDuration: {
    marginTop: 4,
    fontSize: 13,
    color: '#cccccc',
  },
  errorContainer: {
    backgroundColor: '#331111',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  errorText: {
    color: '#ff9999',
    marginBottom: 8,
    fontSize: 13,
  },
  retryButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#6C63FF',
  },
  retryButtonText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  emptyStateContainer: {
    backgroundColor: '#111111',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  emptyStateText: {
    color: '#cccccc',
    fontSize: 14,
  },
});

