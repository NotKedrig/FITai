# Full end-to-end test:
# Register → Login → Start workout → Get exercise → Log Set 1 → Log Set 2 → End workout → Get workout

$ErrorActionPreference = "Stop"

$Base = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:8000" }

Write-Host "======================================"
Write-Host "FITAI END-TO-END RECOMMENDATION TEST"
Write-Host "======================================"

# --------------------------------------------------
# 1. Register
# --------------------------------------------------

Write-Host "`n=== 1. Register ==="

$email = "test$(Get-Random)@example.com"
$username = "testuser$(Get-Random)"
$password = "secret123"

$regBody = @{
    email = $email
    username = $username
    password = $password
} | ConvertTo-Json

$reg = Invoke-RestMethod `
    -Uri "$Base/api/v1/auth/register" `
    -Method Post `
    -ContentType "application/json" `
    -Body $regBody

$reg | ConvertTo-Json -Depth 5
$userId = $reg.id

Write-Host "Registered user: $email"


# --------------------------------------------------
# 2. Login
# --------------------------------------------------

Write-Host "`n=== 2. Login ==="

$loginBody = "email=$email&password=$password"

$login = Invoke-RestMethod `
    -Uri "$Base/api/v1/auth/login" `
    -Method Post `
    -ContentType "application/x-www-form-urlencoded" `
    -Body $loginBody

$login | ConvertTo-Json -Depth 5
$token = $login.access_token

Write-Host "Token acquired."


# --------------------------------------------------
# 3. Start workout
# --------------------------------------------------

Write-Host "`n=== 3. Start workout ==="

$startBody = @{
    name = "AI Test Workout"
    notes = "Testing recommendation system"
} | ConvertTo-Json

$start = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts" `
    -Method Post `
    -Headers @{ Authorization = "Bearer $token" } `
    -ContentType "application/json" `
    -Body $startBody

$start | ConvertTo-Json -Depth 5

$workoutId = $start.id

Write-Host "Workout ID: $workoutId"


# --------------------------------------------------
# 4. Get workout
# --------------------------------------------------

Write-Host "`n=== 4. Get workout ==="

$workout = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $token" }

$workout | ConvertTo-Json -Depth 5


# --------------------------------------------------
# 5. Get Bench Press exercise ID
# --------------------------------------------------

Write-Host "`n=== 5. Get Bench Press exercise ID ==="

$exercises = Invoke-RestMethod `
    -Uri "$Base/api/v1/exercises" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $token" }

$bench = $exercises | Where-Object { $_.name -eq "Bench Press" }

if (-not $bench) {
    Write-Host "ERROR: Bench Press exercise not found."
    Write-Host "Available exercises:"
    $exercises | ForEach-Object { Write-Host " - $($_.name)" }
    exit 1
}

$exerciseId = $bench.id

Write-Host "Exercise ID: $exerciseId"


# --------------------------------------------------
# 6. Log Set 1
# --------------------------------------------------

Write-Host "`n=== 6. Log Set 1 (60kg x 10 @ RPE 6) ==="

$set1Body = @{
    exercise_id = $exerciseId
    weight_kg = 60
    reps = 10
    rpe = 6
    is_warmup = $false
} | ConvertTo-Json

$set1 = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId/sets" `
    -Method Post `
    -Headers @{ Authorization = "Bearer $token" } `
    -ContentType "application/json" `
    -Body $set1Body

$set1 | ConvertTo-Json -Depth 5

if ($set1.recommendation) {
    Write-Host "AI recommendation received."
} else {
    Write-Host "WARNING: No recommendation returned."
}


# --------------------------------------------------
# 7. Log Set 2
# --------------------------------------------------

Write-Host "`n=== 7. Log Set 2 (62.5kg x 8 @ RPE 7.5) ==="

$set2Body = @{
    exercise_id = $exerciseId
    weight_kg = 62.5
    reps = 8
    rpe = 7.5
    is_warmup = $false
} | ConvertTo-Json

$set2 = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId/sets" `
    -Method Post `
    -Headers @{ Authorization = "Bearer $token" } `
    -ContentType "application/json" `
    -Body $set2Body

$set2 | ConvertTo-Json -Depth 5

if ($set2.recommendation) {
    Write-Host "AI recommendation received."
} else {
    Write-Host "WARNING: No recommendation returned."
}


# --------------------------------------------------
# 8. End workout
# --------------------------------------------------

Write-Host "`n=== 8. End workout ==="

$end = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId/end" `
    -Method Post `
    -Headers @{ Authorization = "Bearer $token" }

$end | ConvertTo-Json -Depth 5


# --------------------------------------------------
# 9. Get workout again
# --------------------------------------------------

Write-Host "`n=== 9. Get workout again ==="

$workoutFinal = Invoke-RestMethod `
    -Uri "$Base/api/v1/workouts/$workoutId" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $token" }

$workoutFinal | ConvertTo-Json -Depth 5


Write-Host "`n======================================"
Write-Host "TEST COMPLETE"
Write-Host "======================================"