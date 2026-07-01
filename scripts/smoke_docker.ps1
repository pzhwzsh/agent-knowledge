param(
    [switch]$ValidateOnly,
    [switch]$SkipBuild,
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[smoke] $Message"
}

function Invoke-JsonRequest {
    param(
        [string]$Method,
        [string]$Uri,
        [object]$Body = $null,
        [hashtable]$Headers = @{}
    )

    $params = @{
        Method = $Method
        Uri = $Uri
        Headers = $Headers
    }
    if ($null -ne $Body) {
        $params["Body"] = ($Body | ConvertTo-Json -Depth 20)
        $params["ContentType"] = "application/json"
    }
    return Invoke-RestMethod @params
}

function Write-DockerDiagnostics {
    Write-Step "collecting docker diagnostics"
    & docker compose ps
    & docker compose logs --no-color --tail=120 api worker beat postgres redis
}

function Invoke-SmokeStep {
    param(
        [string]$Description,
        [scriptblock]$Action
    )

    try {
        Write-Step $Description
        return & $Action
    } catch {
        Write-DockerDiagnostics
        throw
    }
}

function Wait-Until {
    param(
        [scriptblock]$Probe,
        [string]$Description,
        [int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $result = & $Probe
            if ($result) {
                return $result
            }
        } catch {
            Start-Sleep -Seconds 2
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "Timed out waiting for $Description"
}

if ($ValidateOnly) {
    Write-Step "script parsed successfully"
    exit 0
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path ".env.example")) {
    throw "Run this script from the repository root or keep it under scripts/."
}

$composeArgs = @("compose")
if ($SkipBuild) {
    $composeArgs += @("up", "-d", "postgres", "redis", "api", "worker", "beat")
} else {
    $composeArgs += @("up", "-d", "--build", "postgres", "redis", "api", "worker", "beat")
}

Write-Step "starting docker compose core services"
& docker @composeArgs

Write-Step "waiting for API health"
Wait-Until -Description "API /health" -TimeoutSeconds $TimeoutSeconds -Probe {
    $health = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/health"
    return $health.status -eq "ok"
} | Out-Null

Write-Step "running Alembic migrations"
& docker compose exec -T api alembic upgrade head

Invoke-SmokeStep "checking pgvector extension" {
    $pgvector = & docker compose exec -T postgres psql -U postgres -d personal_knowledge_radar -tAc "SELECT extname FROM pg_extension WHERE extname = 'vector';"
    if ($pgvector.Trim() -ne "vector") {
        throw "pgvector extension is not installed in the target database"
    }
} | Out-Null

Write-Step "registering smoke user"
$email = "smoke+$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())@example.com"
$password = "password123"
Invoke-JsonRequest -Method Post -Uri "http://localhost:8000/api/auth/register" -Body @{ email = $email; password = $password; display_name = "Smoke User" } | Out-Null
$tokenResponse = Invoke-JsonRequest -Method Post -Uri "http://localhost:8000/api/auth/login" -Body @{ email = $email; password = $password }
$headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }

Invoke-SmokeStep "checking authenticated task schedule endpoint" {
    $schedule = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/tasks/schedule" -Headers $headers
    if (-not $schedule.beat_schedule -or $schedule.beat_schedule.Count -lt 1) {
        throw "Task schedule endpoint returned no beat schedules"
    }
} | Out-Null

$queued = Invoke-SmokeStep "submitting asynchronous ingestion job" {
    $created = Invoke-JsonRequest -Method Post -Uri "http://localhost:8000/api/ingestions" -Headers $headers -Body @{
        input_type = "text"
        input_value = "Docker smoke test content for personal knowledge radar, celery worker, and structured summary."
    }
    if ($created.job.status -ne "pending" -and $created.job.status -ne "failed") {
        throw "Unexpected initial ingestion status: $($created.job.status)"
    }
    if ($created.job.status -eq "failed") {
        throw "Ingestion failed to enqueue: $($created.job.error_message)"
    }
    return $created
}

Write-Step "polling ingestion job"
$jobId = $queued.job.id
$job = Wait-Until -Description "ingestion job completion" -TimeoutSeconds $TimeoutSeconds -Probe {
    $current = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/ingestions/$jobId" -Headers $headers
    if ($current.status -in @("success", "failed")) {
        return $current
    }
    return $null
}
if ($job.status -ne "success") {
    throw "Ingestion job did not succeed: $($job.error_message)"
}

Invoke-SmokeStep "checking authenticated task worker health" {
    $taskHealth = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/tasks/health" -Headers $headers
    if ($taskHealth.workers_online -lt 1) {
        throw "No Celery workers online"
    }
} | Out-Null

Write-Step "smoke test passed"
