# Test sequence: Register -> Login -> Start workout -> Log Set 1 (Bench Press) -> Log Set 2
# Requires: API running (e.g. in Docker or uvicorn app.main:app), DATABASE_URL, GEMINI_API_KEY (or AI will fallback)
# Usage: From fitai-backend, run: .\scripts\test_set_recommendation_flow.ps1
# Set $BaseUrl to match your API (e.g. http://localhost:8000/api/v1).

$ErrorActionPreference = "Stop"
$BaseUrl = "http://localhost:8000/api/v1"
$ExerciseName = "Bench Press"

# 1. Register user (or skip if already registered)
$registerBody = @{
    email    = "test-set@example.com"
    username = "testsetuser"
    password = "testpass123"
} | ConvertTo-Json

Write-Host "1. Register user..."
try {
    $reg = Invoke-RestMethod -Uri "$BaseUrl/auth/register" -Method Post -Body $registerBody -ContentType "application/json"
    Write-Host "   Registered."
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 400 -and $_.ErrorDetails.Message -match "already registered") {
        Write-Host "   User already exists, continuing with login..."
    } else {
        Write-Host "ERROR: Register failed. $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
        throw
    }
}

# 2. Login, get token
Write-Host "2. Login..."
$loginBody = "email=test-set%40example.com&password=testpass123"
$tokenResp = Invoke-RestMethod -Uri "$BaseUrl/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded"
$token = $tokenResp.access_token
$headers = @{ Authorization = "Bearer $token" }

# 3. Start workout
Write-Host "3. Start workout..."
$workoutBody = "{}"
$workout = Invoke-RestMethod -Uri "$BaseUrl/workouts" -Method Post -Headers $headers -Body $workoutBody -ContentType "application/json"
$workoutId = $workout.id
Write-Host "   Workout ID: $workoutId"

# Get exercise ID by name: GET /api/v1/exercises, find name == "Bench Press"
Write-Host "   Fetching exercises (GET /api/v1/exercises)..."
$exercises = Invoke-RestMethod -Uri "$BaseUrl/exercises" -Method Get
$exercise = $exercises | Where-Object { $_.name -eq $ExerciseName } | Select-Object -First 1
if (-not $exercise) {
    Write-Host "ERROR: Exercise '$ExerciseName' not found." -ForegroundColor Red
    Write-Host "Available exercise names:" -ForegroundColor Yellow
    $exercises | ForEach-Object { Write-Host "  - $($_.name)" }
    exit 1
}
$exerciseId = $exercise.id
Write-Host "   Exercise ID ($ExerciseName): $exerciseId"

# 4. Log Set 1: 60kg, 10 reps, RPE 6
Write-Host "4. Log Set 1: $ExerciseName, 60kg x 10 reps RPE 6..."
$set1Body = @{
    exercise_id = $exerciseId
    weight_kg    = 60
    reps        = 10
    rpe         = 6
    is_warmup   = $false
} | ConvertTo-Json
try {
    $set1Resp = Invoke-RestMethod -Uri "$BaseUrl/workouts/$workoutId/sets" -Method Post -Headers $headers -Body $set1Body -ContentType "application/json"
} catch {
    Write-Host "ERROR: Failed to log set 1. $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Response body:" -ForegroundColor Yellow
        Write-Host $_.ErrorDetails.Message
        Write-Host "Tip: If the error mentions a missing column (e.g. confidence), run migrations: alembic upgrade head" -ForegroundColor Cyan
    }
    exit 1
}
if (-not $set1Resp.set) {
    Write-Host "ERROR: Response missing 'set'. Got: $($set1Resp | ConvertTo-Json -Compress)" -ForegroundColor Red
    exit 1
}
Write-Host "   FULL JSON response (Set 1):"
$set1Resp | ConvertTo-Json -Depth 10
if ($set1Resp.recommendation) {
    Write-Host "   Recommendation (next set):" -ForegroundColor Green
    $set1Resp.recommendation | ConvertTo-Json
} else {
    Write-Host "   (No recommendation - e.g. warmup or AI fallback stored only)" -ForegroundColor Gray
}

# 5. Log Set 2: 62.5kg, 8 reps, RPE 7.5
Write-Host "5. Log Set 2: same exercise, 62.5kg x 8 reps RPE 7.5..."
$set2Body = @{
    exercise_id = $exerciseId
    weight_kg    = 62.5
    reps        = 8
    rpe         = 7.5
    is_warmup   = $false
} | ConvertTo-Json
try {
    $set2Resp = Invoke-RestMethod -Uri "$BaseUrl/workouts/$workoutId/sets" -Method Post -Headers $headers -Body $set2Body -ContentType "application/json"
} catch {
    Write-Host "ERROR: Failed to log set 2. $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Response body:" -ForegroundColor Yellow
        Write-Host $_.ErrorDetails.Message
    }
    exit 1
}
if (-not $set2Resp.set) {
    Write-Host "ERROR: Response missing 'set'. Got: $($set2Resp | ConvertTo-Json -Compress)" -ForegroundColor Red
    exit 1
}
Write-Host "   Recommendation for Set 2 (next set suggestion):"
$set2Resp.recommendation | ConvertTo-Json
Write-Host "   Full Set 2 response:"
$set2Resp | ConvertTo-Json -Depth 10

Write-Host "Done. Response includes 'set' and 'recommendation'. Set 2 recommendation is based on Set 1 + Set 2 in current session." -ForegroundColor Green
