#!/usr/bin/env python3
"""One-time E2E health check."""
import json
import os
import sys
from datetime import datetime, timezone

import requests

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
API = f"{BASE}/api/v1"

def main():
    ts = int(datetime.now(timezone.utc).timestamp())
    email = f"e2e_{ts}@fitai-healthcheck.local"
    username = f"e2euser_{ts}"
    password = "HealthCheck2025!"

    print("=== STEP 1 — DOCKER (manual) ===\n")

    print("=== STEP 2 — REGISTER ===")
    r = requests.post(f"{API}/auth/register", json={"email": email, "username": username, "password": password}, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type', 'N/A')}")
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print("Response body:", repr(r.text[:1000]) if r.text else "(empty)")
    if r.status_code != 201:
        sys.exit(1)
    user_id = r.json()["id"]
    print(f"\nUser ID: {user_id}\n")

    print("=== STEP 3 — LOGIN ===")
    r = requests.post(f"{API}/auth/login", data={"email": email, "password": password}, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    if r.status_code != 200:
        sys.exit(1)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print()

    print("=== STEP 4 — EXERCISES ===")
    r = requests.get(f"{API}/exercises", headers=headers, timeout=30)
    print(f"Status: {r.status_code}")
    exs = r.json()
    print(json.dumps(exs, indent=2))
    compound = next((e for e in exs if e.get("is_compound")), exs[0] if exs else None)
    if not compound:
        print("No exercises found"); sys.exit(1)
    exercise_id = compound["id"]
    print(f"\nPicked: {compound['name']} (compound={compound.get('is_compound')}) ID: {exercise_id}\n")

    print("=== STEP 5 — START WORKOUT ===")
    r = requests.post(f"{API}/workouts", headers=headers, json={"name": "E2E Health Check Workout"}, timeout=30)
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    if r.status_code != 201:
        sys.exit(1)
    workout_id = r.json()["id"]
    print(f"\nWorkout ID: {workout_id}\n")

    print("=== STEP 6a — SET 1 (80kg x 5 RPE 7) ===")
    r = requests.post(f"{API}/workouts/{workout_id}/sets", headers=headers, json={"exercise_id": exercise_id, "weight_kg": 80, "reps": 5, "rpe": 7, "is_warmup": False}, timeout=60)
    print(f"Status: {r.status_code}")
    s1 = r.json()
    print(json.dumps(s1, indent=2))
    if r.status_code != 201:
        sys.exit(1)
    rec1 = s1.get("recommendation")
    if rec1:
        print(f"  model_used: {rec1.get('model_used')}")
        print(f"  suggested: {rec1.get('suggested_weight_kg')} kg x {rec1.get('suggested_reps')} reps")
        print(f"  latency_ms: {rec1.get('latency_ms')}")
    print()

    print("=== STEP 6b — SET 2 (82.5kg x 5 RPE 8) ===")
    r = requests.post(f"{API}/workouts/{workout_id}/sets", headers=headers, json={"exercise_id": exercise_id, "weight_kg": 82.5, "reps": 5, "rpe": 8, "is_warmup": False}, timeout=60)
    print(f"Status: {r.status_code}")
    s2 = r.json()
    print(json.dumps(s2, indent=2))
    if r.status_code != 201:
        sys.exit(1)
    rec2 = s2.get("recommendation")
    if rec2:
        print(f"  explanation: {rec2.get('explanation', '')[:120]}...")
    print()

    print("=== STEP 6c — SET 3 (warmup) ===")
    r = requests.post(f"{API}/workouts/{workout_id}/sets", headers=headers, json={"exercise_id": exercise_id, "weight_kg": 60, "reps": 10, "rpe": None, "is_warmup": True}, timeout=30)
    print(f"Status: {r.status_code}")
    s3 = r.json()
    print(json.dumps(s3, indent=2))
    if r.status_code != 201:
        sys.exit(1)
    print(f"  recommendation is null: {s3.get('recommendation') is None}\n")

    print("=== STEP 7 — END WORKOUT (PATCH) ===")
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    r = requests.patch(f"{API}/workouts/{workout_id}", headers=headers, json={"ended_at": now}, timeout=30)
    print(f"Status: {r.status_code}")
    w = r.json()
    print(json.dumps(w, indent=2))
    if r.status_code != 200:
        sys.exit(1)
    print(f"\nended_at populated: {w.get('ended_at') is not None}\n")

    print("=== STEP 8 — DB QUERY (run manually) ===")
    print(f"User ID: {user_id}")
    print("SELECT r.recommended_weight, r.recommended_reps, r.explanation,")
    print("       r.ai_provider, r.model_used, r.confidence, r.latency_ms")
    print("FROM recommendations r")
    print(f"WHERE r.user_id = '{user_id}'")
    print("ORDER BY r.created_at DESC;")

if __name__ == "__main__":
    main()
