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
  sets: [],
  isLogging: false,
  logSetError: null,
  initWorkout: () => {},
  logSet: async () => {},
  removeSet: async () => {},
  clearWorkout: () => {},
});

export function WorkoutProvider({ children }) {
  const { token } = useContext(AuthContext);
  const [workout, setWorkout] = useState(null);
  const [sets, setSets] = useState([]);
  const [isLogging, setIsLogging] = useState(false);
  const [logSetError, setLogSetError] = useState(null);

  const initWorkout = useCallback((workoutFromRoute) => {
    setWorkout(workoutFromRoute || null);
    setSets([]);
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
        setSets((current) => [...current, entry]);
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
        setSets((current) => current.filter((entry) => entry.set.id !== setId));
      } catch (error) {
        // Keep current sets; caller can choose to show error if desired.
        throw error;
      }
    },
    [token],
  );

  const clearWorkout = useCallback(() => {
    setWorkout(null);
    setSets([]);
    setIsLogging(false);
    setLogSetError(null);
  }, []);

  const value = useMemo(
    () => ({
      workout,
      sets,
      isLogging,
      logSetError,
      initWorkout,
      logSet,
      removeSet,
      clearWorkout,
    }),
    [
      workout,
      sets,
      isLogging,
      logSetError,
      initWorkout,
      logSet,
      removeSet,
      clearWorkout,
    ],
  );

  return (
    <WorkoutContext.Provider value={value}>{children}</WorkoutContext.Provider>
  );
}
