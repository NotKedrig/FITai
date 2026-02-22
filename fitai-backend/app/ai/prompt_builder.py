"""Prompt building for AI set recommendations."""

from app.ai.base import WorkoutContext


class PromptBuilder:
    """Builds system and user prompts for recommendation requests."""

    SYSTEM_PROMPT: str = (
    "You are an expert strength coach specializing in strength and hypertrophy training. "
    "Your job is to recommend the NEXT SET ONLY (weight in kg and number of reps) "
    "based on the athlete's context: exercise, current session sets, recent session history, "
    "estimated 1RM, personal best, and fatigue signals (total sets today, workout duration).\n\n"

    "CRITICAL OUTPUT RULES:\n"
    "- You must respond with ONLY valid JSON.\n"
    "- Do NOT include markdown, code fences, or explanatory text outside the JSON.\n"
    "- Your entire response must be exactly one JSON object matching the requested schema.\n"
    "- Do NOT recommend multiple sets.\n"
    "- Do NOT recommend a full workout.\n\n"

    "WEIGHT AND REP CONSTRAINTS:\n"
    "- All weights must be in kilograms (kg).\n"
    "- All rep counts must be integers.\n"
    "- Weight must be a realistic gym load.\n"
    "- Only use increments of 1.25 kg.\n"
    "- Never suggest impossible weights like 83.7 kg.\n\n"

    "COACHING GUIDELINES:\n"
    "- Base recommendations on the athlete's demonstrated strength and fatigue.\n"
    "- Prefer conservative progression when fatigue is high.\n"
    "- Do not increase weight aggressively if recent sets were near failure.\n"
)

    @classmethod
    def build_recommendation_prompt(cls, ctx: WorkoutContext) -> str:
        """Build the user prompt for a single set recommendation."""
        lines = [
            "Recommend the next set for this exercise.",
            "",
            "--- Exercise ---",
            f"Exercise: {ctx.exercise_name}",
            f"Muscle group: {ctx.muscle_group}",
            f"Equipment: {ctx.equipment_type}",
            f"Compound movement: {ctx.is_compound}",
            "",
        ]

        if ctx.estimated_1rm is not None:
            lines.append(f"Estimated 1RM: {ctx.estimated_1rm} kg")
        else:
            lines.append("Estimated 1RM: not available")
        if ctx.max_weight_ever is not None:
            lines.append(f"Personal best (max weight ever): {ctx.max_weight_ever} kg")
        else:
            lines.append("Personal best: not available")
        lines.append("")

        lines.append("--- Current session sets (this exercise) ---")
        if ctx.current_session_sets:
            lines.append(cls._format_current_sets(ctx.current_session_sets))
        else:
            lines.append("No sets completed yet this session.")
        lines.append("")

        lines.append("--- Recent session history (last 3 sessions for this exercise) ---")
        if ctx.recent_sessions:
            lines.append(cls._format_session_history(ctx.recent_sessions))
        else:
            lines.append("No recent session data.")
        lines.append("")

        lines.append("--- Fatigue / workload today ---")
        lines.append(f"Total sets completed today (all exercises): {ctx.total_sets_today}")
        lines.append(f"Workout duration so far: {ctx.workout_duration_minutes} minutes")
        lines.append("")

        lines.append(
            "Respond with ONLY a JSON object with exactly these keys (no other keys, no extra text):"
        )
        lines.append('  "suggested_weight_kg": <number in kg, e.g. 82.5>,')
        lines.append('  "suggested_reps": <integer number of reps>,')
        lines.append('  "explanation": "<short reason for this recommendation>",')
        lines.append('  "confidence": "<one of: high | medium | low>"')
        return "\n".join(lines)

    @staticmethod
    def _format_current_sets(sets: list[dict]) -> str:
        """Format current session sets for the prompt."""
        out = []
        for s in sets:
            weight = s.get("weight_kg", "?")
            reps = s.get("reps", "?")
            rpe = s.get("rpe")
            num = s.get("set_number", "?")
            rpe_str = f" RPE {rpe}" if rpe is not None else ""
            out.append(f"  Set {num}: {weight} kg x {reps} reps{rpe_str}")
        return "\n".join(out) if out else "  (none)"

    @staticmethod
    def _format_session_history(sessions: list[dict]) -> str:
        """Format recent session history for the prompt."""
        out = []
        for i, session in enumerate(sessions, 1):
            parts = [f"  Session {i}:"]
            if "date" in session:
                parts.append(f" date={session['date']}")
            if "sets" in session:
                set_strs = []
                for s in session["sets"]:
                    w = s.get("weight_kg", "?")
                    r = s.get("reps", "?")
                    rpe = s.get("rpe")
                    rpe_str = f" RPE {rpe}" if rpe is not None else ""
                    set_strs.append(f"{w} kg x {r} reps{rpe_str}")
                parts.append(" " + "; ".join(set_strs))
            out.append("".join(parts).strip())
        return "\n".join(out) if out else "  (none)"
