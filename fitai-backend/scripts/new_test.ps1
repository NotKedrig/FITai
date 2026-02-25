# FitAI Full Flow Test
# Tests: Register -> Login -> Start Workout -> Log Sets -> Get Recommendations -> Delete Set -> End Workout

$ErrorActionPreference = "Stop"
$Base = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:8000" }

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "FITAI FULL FLOW TEST" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# --------------------------------------------------
# 1. Register new random user
# --------------------------------------------------
Write-Host "`n=== 1. Register ===" -ForegroundColor Yellow

$email    = "user$(Get-Random)@fitai.com"
$username = "fituser$(Get-Random)"
$password = "testpass123"

$reg = Invoke-RestMethod `
    -Uri "$Base/api/v1/auth/register" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{ email = $email; username = $username; password = $password } | ConvertTo-Json)

$reg | ConvertTo-Json -Depth 5
Write-Host "Registered: $email" -ForegroundColor Green

# --------------------------------------------------
# 2. Login
# --------------------------------------------------
Write-Host "`n=== 2. Login ===" -ForegroundColor Yellow

$login = Invoke-RestMethod `
    -Uri "$Base/api/v1/auth/login" `
    -Method Post `
    -ContentType "application/x-www-form-urlencoded" `
    -Body "email=$email&password=$password"

$login | ConvertTo-Json -Depth 5
$token   = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
Write-Host "Token acquired." -ForegroundColor Green

# --------------------------------------------------
# 3. Start workout
# --------------------------------------------------
Write-Host "`n=== 3. Start Workout ===" -ForegroundColor Yellow

$workout = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ name = "Push Day"; notes = "Full flow test" } | ConvertTo-Json)

$workout | ConvertTo-Json -Depth 5
$workoutId = $workout.id
Write-Host "Workout ID: $workoutId" -ForegroundColor Green

# --------------------------------------------------
# 4. Get exercise (Bench Press)
# --------------------------------------------------
Write-Host "`n=== 4. Get Exercise ===" -ForegroundColor Yellow

$exercises  = Invoke-RestMethod -Uri "$Base/api/v1/exercises" -Method Get -Headers $headers
$bench      = $exercises | Where-Object { $_.name -eq "Barbell Bench Press" } | Select-Object -First 1

if (-not $bench) {
    Write-Host "Bench Press not found. Available exercises:" -ForegroundColor Red
    $exercises | ForEach-Object { Write-Host "  - $($_.name)" }
    exit 1
}

$exerciseId = $bench.id
Write-Host "Exercise: $($bench.name) | ID: $exerciseId" -ForegroundColor Green

# --------------------------------------------------
# 5. Log Set 1 (working set, should trigger AI/rule engine)
# --------------------------------------------------
Write-Host "`n=== 5. Log Set 1 (60kg x 10 @ RPE 6) ===" -ForegroundColor Yellow

$set1 = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId/sets" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ exercise_id = $exerciseId; weight_kg = 60; reps = 10; rpe = 6; is_warmup = $false } | ConvertTo-Json)

$set1 | ConvertTo-Json -Depth 10
$set1Id = $set1.set.id

Write-Host "`nSet 1 ID: $set1Id" -ForegroundColor Green
if ($set1.recommendation) {
    Write-Host "Recommendation received:" -ForegroundColor Green
    Write-Host "  Suggested weight : $($set1.recommendation.suggested_weight_kg) kg"
    Write-Host "  Suggested reps   : $($set1.recommendation.suggested_reps)"
    Write-Host "  Confidence       : $($set1.recommendation.confidence)"
    Write-Host "  Model used       : $($set1.recommendation.model_used)"
    Write-Host "  Latency          : $($set1.recommendation.latency_ms) ms"
    Write-Host "  Explanation      : $($set1.recommendation.explanation)"
} else {
    Write-Host "WARNING: No recommendation returned for Set 1." -ForegroundColor Red
}

# --------------------------------------------------
# 6. Log Set 2 (should use Set 1 as context)
# --------------------------------------------------
Write-Host "`n=== 6. Log Set 2 (62.5kg x 8 @ RPE 7.5) ===" -ForegroundColor Yellow

$set2 = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId/sets" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ exercise_id = $exerciseId; weight_kg = 62.5; reps = 8; rpe = 7.5; is_warmup = $false } | ConvertTo-Json)

$set2 | ConvertTo-Json -Depth 10
$set2Id = $set2.set.id

Write-Host "`nSet 2 ID: $set2Id" -ForegroundColor Green
if ($set2.recommendation) {
    Write-Host "Recommendation received:" -ForegroundColor Green
    Write-Host "  Suggested weight : $($set2.recommendation.suggested_weight_kg) kg"
    Write-Host "  Suggested reps   : $($set2.recommendation.suggested_reps)"
    Write-Host "  Confidence       : $($set2.recommendation.confidence)"
    Write-Host "  Model used       : $($set2.recommendation.model_used)"
    Write-Host "  Latency          : $($set2.recommendation.latency_ms) ms"
    Write-Host "  Explanation      : $($set2.recommendation.explanation)"
} else {
    Write-Host "WARNING: No recommendation returned for Set 2." -ForegroundColor Red
}

# --------------------------------------------------
# 7. Log warmup set (recommendation should be null)
# --------------------------------------------------
Write-Host "`n=== 7. Log Warmup Set (40kg x 10, is_warmup=true) ===" -ForegroundColor Yellow

$warmup = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId/sets" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ exercise_id = $exerciseId; weight_kg = 40; reps = 10; rpe = $null; is_warmup = $true } | ConvertTo-Json)

$warmup | ConvertTo-Json -Depth 10

if ($null -eq $warmup.recommendation) {
    Write-Host "PASS: Warmup set returned null recommendation." -ForegroundColor Green
} else {
    Write-Host "FAIL: Warmup set should return null recommendation." -ForegroundColor Red
}

# --------------------------------------------------
# 8. Delete Set 2
# --------------------------------------------------
Write-Host "`n=== 8. Delete Set 2 ===" -ForegroundColor Yellow

try {
    Invoke-RestMethod `
        -Uri "$Base/api/v1/sets/$set2Id" `
        -Method Delete `
        -Headers $headers

    Write-Host "PASS: Set 2 deleted successfully (204)." -ForegroundColor Green
} catch {
    Write-Host "FAIL: Could not delete Set 2. $($_.Exception.Message)" -ForegroundColor Red
}

# --------------------------------------------------
# 9. End workout
# --------------------------------------------------
Write-Host "`n=== 9. End Workout ===" -ForegroundColor Yellow

try {
    $ended = Invoke-RestMethod `
        -Uri "$Base/api/v1/workouts/$workoutId/end" `
        -Method Post `
        -Headers $headers

    $ended | ConvertTo-Json -Depth 5

    if ($ended.ended_at) {
        Write-Host "PASS: Workout ended at $($ended.ended_at)." -ForegroundColor Green
    } else {
        Write-Host "FAIL: ended_at not populated." -ForegroundColor Red
    }
} catch {
    # Try PATCH if POST /end does not exist
    Write-Host "POST /end failed, trying PATCH..." -ForegroundColor Yellow
    $ended = Invoke-RestMethod `
        -Uri "$Base/api/v1/workouts/$workoutId" `
        -Method Patch `
        -Headers $headers `
        -ContentType "application/json" `
        -Body (@{ ended_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") } | ConvertTo-Json)

    $ended | ConvertTo-Json -Depth 5

    if ($ended.ended_at) {
        Write-Host "PASS: Workout ended at $($ended.ended_at)." -ForegroundColor Green
    } else {
        Write-Host "FAIL: ended_at not populated." -ForegroundColor Red
    }
}

# --------------------------------------------------
# Final Summary
# --------------------------------------------------
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "User         : $email"
Write-Host "Workout ID   : $workoutId"
Write-Host "Set 1 ID     : $set1Id"
Write-Host "Set 2 ID     : $set2Id (deleted)"
Write-Host "Model used   : $($set1.recommendation.model_used)"
Write-Host "======================================" -ForegroundColor Cyan
