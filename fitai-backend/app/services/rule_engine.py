"""Rule-based set recommendation engine — pure logic, no DB or async.

Fatigue scoring: maximum score is 3 (Signals 1–3 only). Signal 4 (duration) is
an exclusive fallback and cannot combine with others. Hard fatigue requires
score >= 2; soft fatigue = 1.
"""

from __future__ import annotations

import math

from app.ai.base import WorkoutContext

# Fatigue signal names for explanation
SIGNAL_REP_DROP = "Rep drop"
SIGNAL_RPE_SPIKE = "RPE spike"
SIGNAL_EXCESSIVE_VOLUME = "Excessive volume"
SIGNAL_DURATION = "Duration"


def _round_weight(weight_kg: float) -> float:
    """Round weight to nearest 1.25 kg. Clamp to >= 0."""
    clamped = max(0.0, weight_kg)
    return round(clamped / 1.25) * 1.25


def _round_training_weight(weight_kg: float, is_compound: bool) -> float:
    """Round training weight with compound vs isolation distinction.

    Compound movements round to the nearest 5 kg.
    Isolation movements round to the nearest 2.5 kg.
    """
    clamped = max(0.0, weight_kg)
    increment = 5.0 if is_compound else 2.5
    return round(clamped / increment) * increment


def _get_delta(is_compound: bool) -> float:
    """Return weight delta: 5.0 for compound, 2.5 for isolation."""
    return 5.0 if is_compound else 2.5


def _apply_1rm_cap(ctx: WorkoutContext, weight: float) -> tuple[float, list[str]]:
    """
    Apply 1RM cap. Returns (clamped weight, extra explanation parts).
    """
    extra: list[str] = []
    if ctx.estimated_1rm is None:
        return (weight, extra)
    cap = math.floor(0.9 * ctx.estimated_1rm / 1.25) * 1.25
    if weight > cap:
        extra.append("Capped at 90% estimated 1RM.")
        return (_round_weight(cap), extra)
    return (weight, extra)


def get_rule_based_recommendation(
    ctx: WorkoutContext,
    last_weight_kg: float,
    last_reps: int,
    last_rpe: float | None,
) -> tuple[float, int, str]:
    """
    Apply rules in strict priority order. Returns (weight, reps, explanation).

    New progression logic:
      - Target RPE is 8, with a working band of 7.5–8.5.
      - Discrete RPE → multiplier mapping pulls loads toward RPE 8.
      - Fatigue signals are detected first, but applied AFTER the multiplier:
          * Hard fatigue (2+ signals at RPE >= 8.5): always reduce by a fixed delta.
          * Soft fatigue (any non-zero signals without hard fatigue): can cap increases.
    """
    is_compound = ctx.is_compound
    parts: list[str] = []

    # Determine whether last set was marked as warmup, if that metadata is present.
    is_warmup = False
    if ctx.current_session_sets:
        last_set = ctx.current_session_sets[-1]
        is_warmup = bool(last_set.get("is_warmup"))

    # Warmups and unknown RPE: maintain load, no progression logic.
    if last_rpe is None or is_warmup:
        suggested_weight = _round_training_weight(last_weight_kg, is_compound)
        suggested_reps = last_reps
        parts.append("Warmup or RPE not provided — maintaining load.")
        suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
        parts.extend(cap_parts)
        parts.append(" | Rule-based suggestion.")
        return (suggested_weight, suggested_reps, " ".join(parts))

    # ── RULE 1: Fatigue detection (signals only; application happens later) ──
    fatigue_signals: list[str] = []

    # Signal 1: Rep drop (2+ sets, drop >= 3)
    if len(ctx.current_session_sets) >= 2:
        prev_reps = ctx.current_session_sets[-2].get("reps")
        if prev_reps is not None and (last_reps - prev_reps) <= -3:
            fatigue_signals.append(SIGNAL_REP_DROP)

    # Signal 2: RPE spike
    if last_rpe is not None and last_rpe >= 9:
        fatigue_signals.append(SIGNAL_RPE_SPIKE)

    # Signal 3: Excessive volume
    if ctx.total_sets_today >= 18:
        fatigue_signals.append(SIGNAL_EXCESSIVE_VOLUME)

    # Signal 4 (duration) is an exclusive fallback. It only contributes to the
    # fatigue score when Signals 1–3 all score 0. It can never combine with
    # other signals to produce hard fatigue.
    if (
        len(fatigue_signals) == 0
        and ctx.workout_duration_minutes is not None
        and ctx.workout_duration_minutes > 120
    ):
        fatigue_signals.append(SIGNAL_DURATION)

    fatigue_count = len(fatigue_signals)
    hard_fatigue = fatigue_count >= 2 and last_rpe is not None and last_rpe >= 8.5
    soft_fatigue = fatigue_count >= 1 and not hard_fatigue

    # ── RULE 2: RIR-based projection toward target RPE 8 ─────────────────────
    target_rpe = 8.0
    target_rir = 10.0 - target_rpe  # = 2

    # Estimate reps to failure at current load using RIR model.
    rir = 10.0 - float(last_rpe)
    est_failure_reps = last_reps + rir
    if est_failure_reps <= 0:
        # Degenerate case: fall back to maintaining load.
        suggested_weight = _round_training_weight(last_weight_kg, is_compound)
        suggested_reps = last_reps
        parts.append(
            "Projected load to target RPE 8 using RIR model, "
            "but failure estimate was invalid — maintaining load."
        )
        suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
        parts.extend(cap_parts)
        parts.append(" | Rule-based suggestion.")
        return (suggested_weight, suggested_reps, " ".join(parts))

    desired_failure_reps = last_reps + target_rir
    intensity_ratio = desired_failure_reps / est_failure_reps
    if intensity_ratio <= 0:
        # Degenerate case: fall back to maintaining load.
        suggested_weight = _round_training_weight(last_weight_kg, is_compound)
        suggested_reps = last_reps
        parts.append(
            "Projected load to target RPE 8 using RIR model, "
            "but intensity ratio was invalid — maintaining load."
        )
        suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
        parts.extend(cap_parts)
        parts.append(" | Rule-based suggestion.")
        return (suggested_weight, suggested_reps, " ".join(parts))

    # Base projection from current RPE toward target RPE 8.
    projected_weight_raw = last_weight_kg / intensity_ratio
    change_pct_raw = (projected_weight_raw - last_weight_kg) / last_weight_kg if last_weight_kg > 0 else 0.0

    clamp_note: str | None = None
    increase_limited_by_soft_fatigue = False

    if change_pct_raw > 0:
        # Clamp maximum increase using dynamic cap scaling based on RPE deficit.
        rpe_deficit = target_rpe - float(last_rpe)
        if rpe_deficit >= 4:
            max_inc = 0.225
        elif rpe_deficit >= 3:
            max_inc = 0.20
        elif rpe_deficit >= 2:
            max_inc = 0.175
        elif rpe_deficit >= 1:
            max_inc = 0.15
        else:
            max_inc = 0.10

        if soft_fatigue and float(last_rpe) >= 8.0:
            max_inc = min(max_inc, 0.075)
            increase_limited_by_soft_fatigue = True

        if change_pct_raw > max_inc:
            change_pct = max_inc
            clamp_note = f"Increase clamped to {max_inc * 100:.1f}% for safety."
        else:
            change_pct = change_pct_raw
    elif change_pct_raw < 0:
        # Clamp maximum decrease (shared for compound/isolation).
        max_dec = 0.10
        if change_pct_raw < -max_dec:
            change_pct = -max_dec
            clamp_note = "Decrease clamped to 10.0% for safety."
        else:
            change_pct = change_pct_raw
    else:
        change_pct = 0.0

    projected_weight = last_weight_kg * (1.0 + change_pct)

    # Explanation for projection.
    parts.append(
        f"Projected load to target RPE 8 using RIR model "
        f"(estimated failure reps ≈ {est_failure_reps:.1f})."
    )
    if clamp_note:
        parts.append(clamp_note)
    if increase_limited_by_soft_fatigue and change_pct > 0:
        parts.append("Soft fatigue detected — projected increase limited to 7.5%.")

    # ── RULE 3: Apply fatigue after projection (hard fatigue overrides) ──────
    if hard_fatigue:
        # Override multiplier: always reduce by a fixed delta based on exercise type.
        delta = _get_delta(is_compound)
        suggested_weight = last_weight_kg - delta
        suggested_weight = _round_training_weight(max(0.0, suggested_weight), is_compound)
        suggested_reps = last_reps
        parts.append(f"{' + '.join(fatigue_signals)}: reducing load by {delta} kg.")
        suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
        parts.extend(cap_parts)
        parts.append(" | Rule-based suggestion.")
        return (suggested_weight, suggested_reps, " ".join(parts))

    # Compute base suggestion from projected weight (already clamped).
    suggested_weight = _round_training_weight(projected_weight, is_compound)
    suggested_reps = last_reps

    # ── Minimum effective change to avoid rounding collapse ──────────────────
    rounded_current = _round_training_weight(last_weight_kg, is_compound)
    delta = _get_delta(is_compound)
    if last_rpe < 7.5 and projected_weight > last_weight_kg and suggested_weight == rounded_current:
        # Force a minimum increase.
        forced_weight = last_weight_kg + delta
        suggested_weight = _round_training_weight(forced_weight, is_compound)
        parts.append(f"Minimum +{delta:g}kg applied to ensure meaningful progression.")

    # ── RULE 4: Session trend (exercise-scoped, high-RPE only) ───────────────
    if len(ctx.current_session_sets) >= 2 and last_rpe is not None and last_rpe >= 8.5:
        current_set = ctx.current_session_sets[-1]
        prev = ctx.current_session_sets[-2]
        current_ex_id = current_set.get("exercise_id")
        prev_ex_id = prev.get("exercise_id")
        if current_ex_id is not None and current_ex_id == prev_ex_id:
            prev_reps = prev.get("reps")
            prev_weight = prev.get("weight_kg")
            same_weight = (
                prev_weight is not None and float(prev_weight) == float(last_weight_kg)
            )
            rep_dropped = (
                prev_reps is not None and last_reps < int(prev_reps)
            )
            if same_weight and rep_dropped and suggested_weight > last_weight_kg:
                suggested_weight = _round_training_weight(last_weight_kg, is_compound)
                suggested_reps = last_reps
                parts.append(
                    "Same-exercise performance dropped at the same weight with high RPE — "
                    "suppressing further increases."
                )

    # ── RULE 5: Recent session comparison (exercise-scoped) ─────────────────
    if ctx.recent_sessions and ctx.current_session_sets:
        current_ex_id = ctx.current_session_sets[-1].get("exercise_id")
        prior_sets = ctx.recent_sessions[0].get("sets", [])
        if current_ex_id is not None and prior_sets:
            same_exercise_sets = [
                s for s in prior_sets if s.get("exercise_id") == current_ex_id
            ]
            if same_exercise_sets:
                best_prior_weight = max(
                    float(s.get("weight_kg", 0)) for s in same_exercise_sets
                )
                if (
                    last_rpe is not None
                    and last_rpe <= 6
                    and last_weight_kg < best_prior_weight
                ):
                    target = max(suggested_weight, best_prior_weight)
                    suggested_weight = _round_training_weight(target, is_compound)
                    parts.append(
                        "Below prior session best for this exercise at low RPE — "
                        "pushing back toward previous best."
                    )

    # ── RULE 6: 1RM cap ─────────────────────────────────────────────────────
    pre_cap_weight = suggested_weight
    suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
    # If cap applied, append concise, non-contradictory messaging.
    if suggested_weight != pre_cap_weight:
        parts.append(
            f"Projected change to {pre_cap_weight:g}kg was capped at 90% estimated 1RM."
        )
    parts.extend(cap_parts)
    parts.append(" | Rule-based suggestion.")
    # Final rounding uses compound/isolation increments.
    suggested_weight = _round_training_weight(suggested_weight, is_compound)
    return (suggested_weight, suggested_reps, " ".join(parts))


def get_minimal_fallback(
    last_weight_kg: float,
    last_reps: int,
    last_rpe: float | None,
) -> tuple[float, int, str]:
    """
    Used when build_context fails and no WorkoutContext is available.
    Preserves original behavior exactly.
    """
    if last_rpe is not None and last_rpe <= 7:
        return (
            last_weight_kg + 2.5,
            last_reps,
            "AI unavailable. Rule-based suggestion.",
        )
    return (
        last_weight_kg,
        last_reps,
        "AI unavailable. Rule-based suggestion.",
    )
