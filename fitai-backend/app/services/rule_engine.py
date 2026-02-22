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

    RPE >= 9 always fires Signal 2 in Rule 1 (fatigue), so Rule 2 never needs
    a decrease outcome for high RPE; only maintain and increase apply.
    """
    is_compound = ctx.is_compound
    parts: list[str] = []

    # ── RULE 1: Fatigue detection ─────────────────────────────────────────────
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

    if hard_fatigue:
        delta = _get_delta(is_compound)
        suggested_weight = last_weight_kg - delta
        suggested_weight = _round_weight(max(0, suggested_weight))
        suggested_reps = last_reps
        parts.append(
            f"{' + '.join(fatigue_signals)}: reducing load by {delta} kg."
        )
        suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
        parts.extend(cap_parts)
        parts.append(" | Rule-based suggestion.")
        return (suggested_weight, suggested_reps, " ".join(parts))

    if soft_fatigue:
        suggested_weight = _round_weight(last_weight_kg)
        suggested_reps = last_reps
        parts.append(fatigue_signals[0])
        parts.append(" — maintaining load.")
        suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
        parts.extend(cap_parts)
        parts.append(" | Rule-based suggestion.")
        return (suggested_weight, suggested_reps, " ".join(parts))

    # No fatigue. Proceed to Rule 2.
    increase_suppressed = False

    # ── RULE 2: RPE bands ────────────────────────────────────────────────────
    # RPE >= 9 always fires Signal 2 in Rule 1, so the decrease branch is
    # unreachable here. Only maintain and increase outcomes apply.
    if last_rpe is None or 7 <= last_rpe <= 8:
        suggested_weight = last_weight_kg
        suggested_reps = last_reps
        parts.append("RPE 7–8 (or unknown) — maintaining load.")
    elif last_rpe <= 6:
        delta = _get_delta(is_compound)
        suggested_weight = last_weight_kg + delta
        suggested_reps = last_reps
        parts.append(f"RPE {int(last_rpe)} — adding {delta} kg ({'compound' if is_compound else 'isolation'}).")
    else:
        # last_rpe in (8, 9); RPE >= 9 never reaches here (Signal 2 fires).
        suggested_weight = last_weight_kg
        suggested_reps = last_reps
        parts.append("RPE 7–8 (or unknown) — maintaining load.")
    suggested_weight = _round_weight(max(0, suggested_weight))

    # ── RULE 3: Session trend (only if 0 fatigue) ─────────────────────────────
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
            suggested_weight = _round_weight(last_weight_kg)
            suggested_reps = last_reps
            parts = [
                "Session trend declining — suppressing increase.",
                f"RPE {int(last_rpe)} noted but overridden.",
            ]

    # ── RULE 4: Recent session comparison ───────────────────────────────────
    if not increase_suppressed and ctx.recent_sessions:
        prior_sets = ctx.recent_sessions[0].get("sets", [])
        if prior_sets:
            best_prior_weight = max(
                float(s.get("weight_kg", 0)) for s in prior_sets
            )
            if last_weight_kg < best_prior_weight and last_rpe is not None and last_rpe <= 6:
                increase_suppressed = True
                suggested_weight = _round_weight(last_weight_kg)
                suggested_reps = last_reps
                parts = [
                    "Current weight below prior session best — suppressing increase.",
                ]

    # If Rule 3 or 4 overrode, parts is already set. Otherwise keep Rule 2 parts.
    # (parts was set in Rule 2, so we're good unless we overwrote)

    # ── RULE 5: 1RM cap ─────────────────────────────────────────────────────
    suggested_weight, cap_parts = _apply_1rm_cap(ctx, suggested_weight)
    parts.extend(cap_parts)
    parts.append(" | Rule-based suggestion.")
    return (_round_weight(suggested_weight), suggested_reps, " ".join(parts))


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
