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
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AuthContext } from '../../context/AuthContext';
import * as exercisesApi from '../../api/exercises';

export default function ExercisePickerScreen() {
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { token } = useContext(AuthContext);

  const [exercises, setExercises] = useState([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadExercises = async () => {
      if (!token) {
        setError('You are not authenticated.');
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const data = await exercisesApi.getExercises(token);
        setExercises(Array.isArray(data) ? data : data?.items || []);
      } catch (err) {
        setError(err.message || 'Failed to load exercises.');
      } finally {
        setIsLoading(false);
      }
    };

    loadExercises();
  }, [token]);

  const filteredExercises = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return exercises;
    return exercises.filter((exercise) => {
      const name = (exercise.name || '').toLowerCase();
      const muscle = (exercise.muscle_group || '').toLowerCase();
      const equipment = (exercise.equipment_type || '').toLowerCase();
      return (
        name.includes(term) ||
        muscle.includes(term) ||
        equipment.includes(term)
      );
    });
  }, [exercises, search]);

  const handleSelectExercise = (exercise) => {
    navigation.navigate('LogSet', { exercise });
  };

  const renderExerciseItem = ({ item }) => {
    return (
      <TouchableOpacity
        style={styles.exerciseItem}
        onPress={() => handleSelectExercise(item)}
        activeOpacity={0.8}
      >
        <Text style={styles.exerciseName}>{item.name}</Text>
        <Text style={styles.exerciseMeta}>
          {(item.muscle_group || 'Unknown muscle').toString()}
          {' · '}
          {(item.equipment_type || 'Bodyweight').toString()}
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={[styles.header, { paddingTop: insets.top + 12 }]}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>‹</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Select Exercise</Text>
          <View style={styles.headerRightPlaceholder} />
        </View>

        <View style={styles.searchContainer}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search exercises..."
            placeholderTextColor="#666666"
            value={search}
            onChangeText={setSearch}
          />
        </View>

        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#6C63FF" />
          </View>
        )}

        {!isLoading && error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {!isLoading && !error && filteredExercises.length === 0 && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No exercises found.</Text>
          </View>
        )}

        {!isLoading && !error && (
          <FlatList
            data={filteredExercises}
            keyExtractor={(item) => String(item.id)}
            renderItem={renderExerciseItem}
            contentContainerStyle={styles.listContent}
          />
        )}
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
  searchContainer: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  searchInput: {
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#333333',
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    backgroundColor: '#111111',
    fontSize: 15,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  errorText: {
    color: '#ff9999',
    fontSize: 13,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  emptyText: {
    color: '#cccccc',
    fontSize: 14,
    textAlign: 'center',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  exerciseItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#222222',
  },
  exerciseName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 2,
  },
  exerciseMeta: {
    fontSize: 13,
    color: '#aaaaaa',
  },
});

