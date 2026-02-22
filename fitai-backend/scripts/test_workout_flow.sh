#!/usr/bin/env bash
set -e

BASE="${BASE_URL:-http://localhost:8000}"
EXERCISE_NAME="Bench Press"

RAND=$RANDOM
EMAIL="test${RAND}@example.com"
USERNAME="testuser${RAND}"
PASSWORD="secret123"

echo "======================================"
echo "FITAI AI RECOMMENDATION TEST"
echo "======================================"

# --------------------------------------------------
# 1. Register
# --------------------------------------------------

echo "=== 1. Register ==="

REG=$(curl -s -X POST "$BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

echo "$REG" | python3 -m json.tool

USER_ID=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

echo "User id: $USER_ID"


# --------------------------------------------------
# 2. Login
# --------------------------------------------------

echo ""
echo "=== 2. Login ==="

LOGIN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=$EMAIL&password=$PASSWORD")

echo "$LOGIN" | python3 -m json.tool

TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "Token acquired"


# --------------------------------------------------
# 3. Start workout
# --------------------------------------------------

echo ""
echo "=== 3. Start workout ==="

START=$(curl -s -X POST "$BASE/api/v1/workouts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"AI Test Workout","notes":"Testing recommendations"}')

echo "$START" | python3 -m json.tool

WORKOUT_ID=$(echo "$START" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

echo "Workout id: $WORKOUT_ID"


# --------------------------------------------------
# 4. Get exercise ID
# --------------------------------------------------

echo ""
echo "=== 4. Get exercise ID ==="

EXERCISES=$(curl -s "$BASE/api/v1/exercises" \
  -H "Authorization: Bearer $TOKEN")

EXERCISE_ID=$(echo "$EXERCISES" | python3 -c "
import sys,json
name=sys.argv[1]
data=json.load(sys.stdin)
for e in data:
    if e['name']==name:
        print(e['id'])
        break
else:
    sys.exit(1)
" "$EXERCISE_NAME") || true

if [ -z "$EXERCISE_ID" ]; then
  echo "Exercise not found"
  exit 1
fi

echo "Exercise id: $EXERCISE_ID"


# --------------------------------------------------
# 5. Log Set 1
# --------------------------------------------------

echo ""
echo "=== 5. Log Set 1 ==="

SET1=$(curl -s -X POST "$BASE/api/v1/workouts/$WORKOUT_ID/sets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"exercise_id\":\"$EXERCISE_ID\",\"weight_kg\":60,\"reps\":10,\"rpe\":6,\"is_warmup\":false}")

echo "$SET1" | python3 -m json.tool


# --------------------------------------------------
# 6. Log Set 2
# --------------------------------------------------

echo ""
echo "=== 6. Log Set 2 ==="

SET2=$(curl -s -X POST "$BASE/api/v1/workouts/$WORKOUT_ID/sets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"exercise_id\":\"$EXERCISE_ID\",\"weight_kg\":62.5,\"reps\":8,\"rpe\":7.5,\"is_warmup\":false}")

echo "$SET2" | python3 -m json.tool


# --------------------------------------------------
# 7. End workout
# --------------------------------------------------

echo ""
echo "=== 7. End workout ==="

END=$(curl -s -X POST "$BASE/api/v1/workouts/$WORKOUT_ID/end" \
  -H "Authorization: Bearer $TOKEN")

echo "$END" | python3 -m json.tool


# --------------------------------------------------
# Done
# --------------------------------------------------

echo ""
echo "======================================"
echo "TEST COMPLETE"
echo "======================================"