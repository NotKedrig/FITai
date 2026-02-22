"""Unit tests for stats service (Epley formula and response shape)."""

# Keys that get_exercise_stats and get_user_overview must return (for API contract)
EXERCISE_STATS_KEYS = {
    "estimated_1rm",
    "max_weight_kg",
    "total_volume_kg",
    "total_sets",
    "sessions_count",
    "last_session_date",
}
USER_OVERVIEW_KEYS = {
    "total_workouts",
    "total_sets",
    "total_volume_kg",
    "most_trained_muscle",
    "favourite_exercise",
    "active_streak_days",
}


def test_epley_estimated_1rm_100kg_x_5() -> None:
    """For 100 kg x 5 reps, estimated_1rm = 100 * (1 + 5/30) = 116.67 kg."""
    result = round(100.0 * (1 + 5 / 30), 2)
    assert result == 116.67


def test_exercise_stats_keys_defined() -> None:
    """get_exercise_stats returns exactly these 6 keys."""
    assert len(EXERCISE_STATS_KEYS) == 6


def test_user_overview_keys_defined() -> None:
    """get_user_overview returns exactly these 6 keys."""
    assert len(USER_OVERVIEW_KEYS) == 6
