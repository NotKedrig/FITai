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

    Compound movements round to the nearest 2.5 kg.
    Isolation movements round to the nearest 1.25 kg.
    """
    clamped = max(0.0, weight_kg)
    increment = 2.5 if is_compound else 1.25
    return round(clamped / increment) * increment


def _get_delta(is_compound: bool) -> float:
    """Return weight delta: 2.5 for compound, 1.25 for isolation."""
    return 2.5 if is_compound else 1.25


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
      - A multiplier table maps discrete RPE values to % changes.
      - Fatigue signals are detected first, but applied AFTER the multiplier:
          * Hard fatigue (2+ signals): always reduce by a fixed delta.
          * Soft fatigue (1 signal): cap increases (multiplier > 1.0) to maintain.
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
    soft_fatigue = fatigue_count == 1
    hard_fatigue = fatigue_count >= 2

    # ── RULE 2: RPE-based multiplier ─────────────────────────────────────────
    target_rpe = 8
    rpe_deficit = target_rpe - float(last_rpe)
    _ = rpe_deficit  # kept for potential future tuning

    rpe_for_text = int(last_rpe) if float(last_rpe).is_integer() else last_rpe

    if last_rpe <= 4:
        multiplier = 1.15
        parts.append(
            f"RPE {rpe_for_text} — significantly underloaded, increasing weight by 15%."
        )
    elif last_rpe == 5:
        multiplier = 1.10
        parts.append(f"RPE {rpe_for_text} — underloaded, increasing by 10%.")
    elif last_rpe == 6:
        multiplier = 1.05
        parts.append(f"RPE {rpe_for_text} — below target, increasing by 5%.")
    elif last_rpe == 7:
        multiplier = 1.025
        parts.append(f"RPE {rpe_for_text} — approaching target, small increase.")
    elif last_rpe == 8:
        multiplier = 1.0
        parts.append(f"RPE {rpe_for_text} — on target. Maintaining load.")
    elif last_rpe == 9:
        multiplier = 0.975
        parts.append(f"RPE {rpe_for_text} — above target, slight reduction.")
    else:  # last_rpe >= 10
        multiplier = 0.95
        parts.append(f"RPE {rpe_for_text} — too close to failure, reducing load.")

    # ── RULE 3: Apply fatigue after multiplier ───────────────────────────────
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

    # Soft fatigue: always record the signal, and cap increases if needed.
    effective_multiplier = multiplier
    if soft_fatigue:
        parts.append(fatigue_signals[0])
        if effective_multiplier > 1.0:
            effective_multiplier = 1.0
            parts.append("— capping at maintain due to fatigue.")

    # Compute base suggestion from effective multiplier.
    suggested_weight = last_weight_kg * effective_multiplier
    suggested_weight = _round_training_weight(suggested_weight, is_compound)
    suggested_reps = last_reps

    # ── Minimum effective change to avoid rounding collapse ──────────────────
    rounded_current = _round_training_weight(last_weight_kg, is_compound)
    delta = _get_delta(is_compound)
    if effective_multiplier > 1.0 and suggested_weight == rounded_current:
        # Force a minimum increase.
        forced_weight = last_weight_kg + delta
        suggested_weight = _round_training_weight(forced_weight, is_compound)
        parts.append(f"Minimum +{delta:g}kg applied.")
    elif effective_multiplier < 1.0 and suggested_weight == rounded_current:
        # Force a minimum reduction.
        forced_weight = last_weight_kg - delta
        suggested_weight = _round_training_weight(forced_weight, is_compound)
        parts.append(f"Minimum -{delta:g}kg applied.")

    # ── RULE 3: Session trend (only if 0 or soft fatigue) ────────────────────
    increase_suppressed = False

    if len(ctx.current_session_sets) >= 2:
        prev = ctx.current_session_sets[-2]
        prev_reps = prev.get("reps")
        prev_weight = prev.get("weight_kg")
        rep_drop = (last_reps - prev_reps) if prev_reps is not None else 0
        weight_dropped = (
            prev_weight is not None and last_weight_kg < float(prev_weight)
        )
        trend_declining = rep_drop <= -2 or weight_dropped
        if trend_declining and last_rpe is not None and last_rpe <= 6:
            increase_suppressed = True
            suggested_weight = _round_training_weight(last_weight_kg, is_compound)
            suggested_reps = last_reps
            parts.append("Session trend declining — suppressing increase.")
            parts.append(f"RPE {int(last_rpe)} noted but overridden.")

    # ── RULE 4: Recent session comparison ───────────────────────────────────
    if not increase_suppressed and ctx.recent_sessions:
        prior_sets = ctx.recent_sessions[0].get("sets", [])
        if prior_sets:
            best_prior_weight = max(
                float(s.get("weight_kg", 0)) for s in prior_sets
            )
            if last_weight_kg < best_prior_weight and last_rpe is not None and last_rpe <= 6:
                increase_suppressed = True
                suggested_weight = _round_training_weight(last_weight_kg, is_compound)
                suggested_reps = last_reps
                parts.append(
                    "Current weight below prior session best — suppressing increase."
                )

    # ── RULE 5: 1RM cap ─────────────────────────────────────────────────────
    pre_cap_weight = suggested_weight
    suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
    # If cap applied and fully blocked an increase (no net change), override explanation.
    if (
        suggested_weight == rounded_current
        and pre_cap_weight != rounded_current
        and effective_multiplier > 1.0
    ):
        parts = [
            f"RPE {rpe_for_text} — below target. "
            f"Attempted increase to {pre_cap_weight:g}kg. "
            f"Capped at 90% estimated 1RM. Maintaining {rounded_current:g}kg."
        ]
    elif suggested_weight != pre_cap_weight:
        parts.append(
            f"Attempted change to {pre_cap_weight:g}kg, capped at 90% estimated 1RM."
        )
        parts.extend(cap_parts)
    else:
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
