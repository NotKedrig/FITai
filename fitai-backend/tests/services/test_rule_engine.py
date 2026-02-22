"""Unit tests for rule-based recommendation engine."""

from app.ai.base import WorkoutContext
from app.services.rule_engine import (
    get_minimal_fallback,
    get_rule_based_recommendation,
)


def build_mock_ctx(
    *,
    exercise_name: str = "Bench Press",
    muscle_group: str = "chest",
    equipment_type: str = "barbell",
    is_compound: bool = True,
    current_session_sets: list[dict] | None = None,
    recent_sessions: list[dict] | None = None,
    estimated_1rm: float | None = None,
    max_weight_ever: float | None = None,
    total_sets_today: int = 5,
    workout_duration_minutes: int | None = 60,
    seconds_since_last_set: int | None = None,
    target_rpe: float | None = None,
) -> WorkoutContext:
    """Construct a WorkoutContext for testing."""
    return WorkoutContext(
        exercise_name=exercise_name,
        muscle_group=muscle_group,
        equipment_type=equipment_type,
        is_compound=is_compound,
        current_session_sets=current_session_sets or [],
        recent_sessions=recent_sessions or [],
        estimated_1rm=estimated_1rm,
        max_weight_ever=max_weight_ever,
        total_sets_today=total_sets_today,
        workout_duration_minutes=workout_duration_minutes or 0,
        seconds_since_last_set=seconds_since_last_set,
        target_rpe=target_rpe,
    )


# ── RPE BAND TESTS (clean context, no fatigue signals) ──────────────────────

def test_rpe_5_compound_increase() -> None:
    """RPE 5, is_compound=True → weight + 2.5 kg."""
    ctx = build_mock_ctx(is_compound=True)
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 10, 5.0)
    assert weight == 62.5
    assert reps == 10


def test_rpe_6_isolation_increase() -> None:
    """RPE 6, is_compound=False → weight + 1.25 kg."""
    ctx = build_mock_ctx(is_compound=False)
    weight, reps, _ = get_rule_based_recommendation(ctx, 20.0, 12, 6.0)
    assert weight == 21.25
    assert reps == 12


def test_rpe_7_maintain() -> None:
    """RPE 7, any → weight maintained."""
    ctx = build_mock_ctx(is_compound=True)
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 7.0)
    assert weight == 60.0
    assert reps == 8


def test_rpe_8_maintain() -> None:
    """RPE 8, any → weight maintained."""
    ctx = build_mock_ctx(is_compound=True)
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 8.0)
    assert weight == 60.0
    assert reps == 8


def test_rpe_none_maintain() -> None:
    """RPE None, any → weight maintained."""
    ctx = build_mock_ctx(is_compound=True)
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, None)
    assert weight == 60.0
    assert reps == 8


def test_rpe_9_no_fatigue_decrease_compound() -> None:
    """RPE 9 fires Signal 2; soft fatigue suppresses Rule 2 decrease."""
    ctx = build_mock_ctx(is_compound=True, total_sets_today=5)
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 9.0)
    assert weight == 60.0  # maintained, not decreased
    assert reps == 8
    assert "RPE spike" in expl


# ── FATIGUE SIGNAL TESTS ────────────────────────────────────────────────────

def test_rep_drop_3_soft_fatigue_maintain() -> None:
    """Rep drop of exactly 3 (last_reps=8, prev_reps=11) → soft fatigue, weight maintained."""
    ctx = build_mock_ctx(
        current_session_sets=[
            {"weight_kg": 60, "reps": 11, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 5, "set_number": 2},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8
    assert "Rep drop" in expl
    assert "maintaining" in expl.lower()


def test_rep_drop_4_soft_fatigue_maintain() -> None:
    """Rep drop of 4 → soft fatigue, weight maintained."""
    ctx = build_mock_ctx(
        current_session_sets=[
            {"weight_kg": 60, "reps": 12, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 5, "set_number": 2},
        ],
    )
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8


def test_rep_drop_2_rule3_session_trend_not_fatigue() -> None:
    """Rep drop of 2 → Rule 3 (session trend), not Rule 1; suppresses increase."""
    ctx = build_mock_ctx(
        current_session_sets=[
            {"weight_kg": 60, "reps": 10, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 5, "set_number": 2},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8
    assert "Session trend" in expl
    assert "Rep drop" not in expl


def test_rpe_9_only_soft_fatigue_maintain() -> None:
    """last_rpe=9 only, no other signals → soft fatigue (1 signal), weight maintained."""
    ctx = build_mock_ctx(total_sets_today=5)
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 9.0)
    assert weight == 60.0
    assert reps == 8
    assert "RPE spike" in expl
    assert "maintaining" in expl.lower()


def test_total_sets_18_soft_fatigue_maintain() -> None:
    """total_sets_today=18, no other signals → soft fatigue, weight maintained."""
    ctx = build_mock_ctx(total_sets_today=18)
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8
    assert "Excessive volume" in expl


def test_total_sets_17_no_fatigue() -> None:
    """total_sets_today=17 → no fatigue signal fires from volume alone."""
    ctx = build_mock_ctx(total_sets_today=17)
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 62.5  # progression allowed
    assert reps == 8


def test_duration_121_only_soft_fatigue() -> None:
    """workout_duration_minutes=121, no other signals → soft fatigue, weight maintained."""
    ctx = build_mock_ctx(workout_duration_minutes=121, total_sets_today=5)
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8
    assert "Duration" in expl


def test_duration_121_plus_rep_drop_3_hard_fatigue() -> None:
    """Duration does not combine with other signals; only rep drop fires, score = 1."""
    ctx = build_mock_ctx(
        workout_duration_minutes=121,
        current_session_sets=[
            {"weight_kg": 60, "reps": 11, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 6, "set_number": 2},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 6.0)
    assert weight == 60.0  # soft fatigue (maintain), not hard fatigue
    assert reps == 8
    assert "Rep drop" in expl


def test_rep_drop_3_and_rpe9_hard_fatigue() -> None:
    """Rep drop of 3 AND last_rpe=9 → 2 signals, hard fatigue, weight - 2.5 kg (compound)."""
    ctx = build_mock_ctx(
        is_compound=True,
        current_session_sets=[
            {"weight_kg": 60, "reps": 11, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 9, "set_number": 2},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 9.0)
    assert weight == 57.5
    assert reps == 8
    assert "Rep drop" in expl
    assert "RPE spike" in expl


def test_all_4_signals_hard_fatigue() -> None:
    """Signals 1, 2, 3 fire (rep drop, RPE spike, excessive volume). Max score = 3."""
    ctx = build_mock_ctx(
        total_sets_today=18,
        workout_duration_minutes=121,
        current_session_sets=[
            {"weight_kg": 60, "reps": 11, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 9, "set_number": 2},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 9.0)
    assert weight == 57.5
    assert reps == 8
    assert "Rep drop" in expl
    assert "RPE spike" in expl
    assert "Excessive volume" in expl


def test_zero_signals_progression_allowed() -> None:
    """0 signals → progression allowed per RPE band."""
    ctx = build_mock_ctx(total_sets_today=5)
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 62.5
    assert reps == 8


# ── DURATION ISOLATION TEST ────────────────────────────────────────────────

def test_duration_isolation_30_vs_150() -> None:
    """duration=30 → increase; duration=150 → maintain (duration signal only)."""
    base = dict(
        current_session_sets=[],
        recent_sessions=[],
        total_sets_today=5,
        is_compound=True,
    )
    ctx_30 = build_mock_ctx(workout_duration_minutes=30, **base)
    ctx_150 = build_mock_ctx(workout_duration_minutes=150, **base)

    weight_30, _, _ = get_rule_based_recommendation(ctx_30, 60.0, 8, 6.0)
    weight_150, _, _ = get_rule_based_recommendation(ctx_150, 60.0, 8, 6.0)

    assert weight_30 == 62.5
    assert weight_150 == 60.0


# ── SESSION TREND TESTS ──────────────────────────────────────────────────────

def test_session_trend_rep_drop_2_suppress() -> None:
    """Rep drop of 2 between last 2 session sets → increase suppressed."""
    ctx = build_mock_ctx(
        current_session_sets=[
            {"weight_kg": 60, "reps": 10, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 5, "set_number": 2},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8
    assert "Session trend" in expl


def test_session_trend_weight_drop_suppress() -> None:
    """Weight drop between last 2 session sets → increase suppressed."""
    ctx = build_mock_ctx(
        current_session_sets=[
            {"weight_kg": 62.5, "reps": 8, "rpe": 7, "set_number": 1},
            {"weight_kg": 60.0, "reps": 8, "rpe": 5, "set_number": 2},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8
    assert "Session trend" in expl


def test_session_trend_stable_no_suppress() -> None:
    """Stable reps and weight → Rule 3 does not suppress."""
    ctx = build_mock_ctx(
        current_session_sets=[
            {"weight_kg": 60, "reps": 8, "rpe": 7, "set_number": 1},
            {"weight_kg": 60, "reps": 8, "rpe": 5, "set_number": 2},
        ],
    )
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 62.5
    assert reps == 8


# ── RECENT SESSION COMPARISON TESTS ─────────────────────────────────────────

def test_recent_session_below_prior_suppress() -> None:
    """last_weight_kg < best set of prior session → increase suppressed."""
    ctx = build_mock_ctx(
        recent_sessions=[
            {"date": "2025-02-20", "sets": [{"weight_kg": 65, "reps": 6, "rpe": 8}]},
        ],
    )
    weight, reps, expl = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 60.0
    assert reps == 8
    assert "prior session" in expl.lower()


def test_recent_session_above_prior_allow() -> None:
    """last_weight_kg >= best set of prior session → progression allowed."""
    ctx = build_mock_ctx(
        recent_sessions=[
            {"date": "2025-02-20", "sets": [{"weight_kg": 55, "reps": 8, "rpe": 7}]},
        ],
    )
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 62.5
    assert reps == 8


def test_no_recent_sessions_rule4_skipped() -> None:
    """No recent sessions → Rule 4 skipped, no effect."""
    ctx = build_mock_ctx(recent_sessions=[])
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 62.5
    assert reps == 8


# ── 1RM CAP TESTS ──────────────────────────────────────────────────────────

def test_1rm_cap_exceeds_clamped() -> None:
    """Suggested weight exceeds 90% 1RM → clamped to correct value."""
    # 1RM=100 → cap = floor(90/1.25)*1.25 = 90. 90+2.5=92.5 exceeds cap.
    ctx = build_mock_ctx(estimated_1rm=100.0)
    weight, reps, expl = get_rule_based_recommendation(ctx, 90.0, 5, 5.0)
    assert weight == 90.0
    assert reps == 5
    assert "90% estimated 1RM" in expl


def test_1rm_cap_below_unchanged() -> None:
    """Suggested weight is below cap → no clamping."""
    ctx = build_mock_ctx(estimated_1rm=100.0)
    weight, reps, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 62.5
    assert reps == 8


def test_estimated_1rm_none_rule5_skipped() -> None:
    """estimated_1rm is None → Rule 5 skipped entirely."""
    ctx = build_mock_ctx(estimated_1rm=None)
    weight, reps, expl = get_rule_based_recommendation(ctx, 200.0, 5, 5.0)
    assert weight == 202.5
    assert reps == 5
    assert "1RM" not in expl


# ── WEIGHT ROUNDING TESTS ───────────────────────────────────────────────────

def test_weight_rounding_multiple_125() -> None:
    """Any output weight must be a multiple of 1.25 kg."""
    ctx = build_mock_ctx()
    weight, _, _ = get_rule_based_recommendation(ctx, 60.0, 8, 5.0)
    assert weight == 62.5
    # 1.25 = 5/4, so weight must equal n/4 for integer n
    assert abs(weight * 4 - round(weight * 4)) < 0.001


def test_weight_never_below_zero() -> None:
    """Weight never goes below 0."""
    ctx = build_mock_ctx(is_compound=True)
    weight, _, _ = get_rule_based_recommendation(ctx, 1.0, 8, 9.0)
    assert weight >= 0


# ── MINIMAL FALLBACK TESTS ──────────────────────────────────────────────────

def test_minimal_fallback_rpe_7() -> None:
    """RPE=7 → weight + 2.5 kg."""
    weight, reps, expl = get_minimal_fallback(60.0, 8, 7.0)
    assert weight == 62.5
    assert reps == 8
    assert "AI unavailable" in expl


def test_minimal_fallback_rpe_6() -> None:
    """RPE=6 → weight + 2.5 kg."""
    weight, reps, _ = get_minimal_fallback(60.0, 8, 6.0)
    assert weight == 62.5
    assert reps == 8


def test_minimal_fallback_rpe_8() -> None:
    """RPE=8 → weight maintained."""
    weight, reps, _ = get_minimal_fallback(60.0, 8, 8.0)
    assert weight == 60.0
    assert reps == 8


def test_minimal_fallback_rpe_10() -> None:
    """RPE=10 → weight maintained."""
    weight, reps, _ = get_minimal_fallback(60.0, 8, 10.0)
    assert weight == 60.0
    assert reps == 8


def test_minimal_fallback_rpe_none() -> None:
    """RPE=None → weight maintained."""
    weight, reps, _ = get_minimal_fallback(60.0, 8, None)
    assert weight == 60.0
    assert reps == 8
