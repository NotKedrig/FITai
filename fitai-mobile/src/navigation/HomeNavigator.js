import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import HomeScreen from '../screens/home/HomeScreen';
import StartWorkoutScreen from '../screens/workout/StartWorkoutScreen';
import ActiveWorkoutScreen from '../screens/workout/ActiveWorkoutScreen';
import ExercisePickerScreen from '../screens/workout/ExercisePickerScreen';
import LogSetScreen from '../screens/workout/LogSetScreen';

const Stack = createStackNavigator();

export default function HomeNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeMain" component={HomeScreen} />
      <Stack.Screen name="StartWorkout" component={StartWorkoutScreen} />
      <Stack.Screen name="ActiveWorkout" component={ActiveWorkoutScreen} />
      <Stack.Screen name="ExercisePicker" component={ExercisePickerScreen} />
      <Stack.Screen name="LogSet" component={LogSetScreen} />
    </Stack.Navigator>
  );
}


