import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import * as setsApi from "../api/sets";
import { AuthContext } from "./AuthContext";

export const WorkoutContext = createContext({
  workout: null,
  exercises: [],
  latestRecommendation: null,
  isLogging: false,
  logSetError: null,
  initWorkout: () => {},
  addExercise: () => {},
  restoreWorkout: () => {},
  logSet: async () => {},
  removeSet: async () => {},
  clearWorkout: () => {},
});

export function WorkoutProvider({ children }) {
  const { token } = useContext(AuthContext);
  const [workout, setWorkout] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [latestRecommendation, setLatestRecommendation] = useState(null);
  const [isLogging, setIsLogging] = useState(false);
  const [logSetError, setLogSetError] = useState(null);

  const initWorkout = useCallback((workoutFromRoute) => {
    setWorkout(workoutFromRoute || null);
    setExercises([]);
    setLatestRecommendation(null);
    setIsLogging(false);
    setLogSetError(null);
  }, []);

  const addExercise = useCallback((exercise) => {
    if (!exercise || !exercise.id) {
      return;
    }
    setExercises((current) => {
      const exists = current.some(
        (block) => block.exercise && block.exercise.id === exercise.id,
      );
      if (exists) {
        return current;
      }
      return [...current, { exercise, sets: [] }];
    });
  }, []);

  const restoreWorkout = useCallback((workoutFromBackend, exerciseGroups) => {
    setWorkout(workoutFromBackend || null);
    const nextExercises =
      Array.isArray(exerciseGroups) && exerciseGroups.length > 0
        ? exerciseGroups.map((group) => ({
            exercise: group.exercise,
            sets: Array.isArray(group.sets)
              ? group.sets.map((set) => ({
                  set,
                  recommendation: null,
                }))
              : [],
          }))
        : [];
    setExercises(nextExercises);
    setLatestRecommendation(null);
    setIsLogging(false);
    setLogSetError(null);
  }, []);

  const logSet = useCallback(
    async (exerciseId, weightKg, reps, rpe, isWarmup) => {
      if (!token || !workout || !workout.id) {
        setLogSetError("No active workout.");
        return;
      }
      setIsLogging(true);
      setLogSetError(null);
      try {
        const result = await setsApi.logSet(
          token,
          workout.id,
          exerciseId,
          weightKg,
          reps,
          rpe,
          isWarmup,
        );
        const entry = {
          set: result.set,
          recommendation: result.recommendation || null,
        };
        setExercises((current) => {
          let found = false;
          const updated = current.map((block) => {
            if (block.exercise && block.exercise.id === exerciseId) {
              found = true;
              return {
                ...block,
                sets: [...block.sets, entry],
              };
            }
            return block;
          });
          if (!found) {
            return [
              ...updated,
              {
                exercise: { id: exerciseId },
                sets: [entry],
              },
            ];
          }
          return updated;
        });

        if (!isWarmup && result.recommendation) {
          setLatestRecommendation(result.recommendation);
        }
      } catch (error) {
        setLogSetError(error.message || "Failed to log set.");
        throw error;
      } finally {
        setIsLogging(false);
      }
    },
    [token, workout],
  );

  const removeSet = useCallback(
    async (setId) => {
      if (!token) {
        return;
      }
      try {
        await setsApi.deleteSet(token, setId);
        setExercises((current) => {
          const updated = current
            .map((block) => ({
              ...block,
              sets: block.sets.filter((entry) => entry.set.id !== setId),
            }))
            .filter((block) => block.sets.length > 0);
          if (updated.length === 0) {
            setLatestRecommendation(null);
          }
          return updated;
        });
      } catch (error) {
        throw error;
      }
    },
    [token],
  );

  const clearWorkout = useCallback(() => {
    setWorkout(null);
    setExercises([]);
    setLatestRecommendation(null);
    setIsLogging(false);
    setLogSetError(null);
  }, []);

  const value = useMemo(
    () => ({
      workout,
      exercises,
      latestRecommendation,
      isLogging,
      logSetError,
      initWorkout,
      addExercise,
      restoreWorkout,
      logSet,
      removeSet,
      clearWorkout,
    }),
    [
      workout,
      exercises,
      latestRecommendation,
      isLogging,
      logSetError,
      initWorkout,
      addExercise,
      restoreWorkout,
      logSet,
      removeSet,
      clearWorkout,
    ],
  );

  return (
    <WorkoutContext.Provider value={value}>{children}</WorkoutContext.Provider>
  );
}
