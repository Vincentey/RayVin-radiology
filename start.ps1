# Radiology AI Assistant - Windows Production Startup Script

Write-Host "=============================================="
Write-Host "  Radiology AI Assistant - Startup"
Write-Host "=============================================="

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy config.example.env to .env and configure your settings:"
    Write-Host "  Copy-Item config.example.env .env"
    Write-Host "  notepad .env"
    exit 1
}

# Load environment variables from .env
Get-Content .env | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

# Validate required variables
$openaiKey = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")
$pineconeKey = [Environment]::GetEnvironmentVariable("PINECONE_API_KEY", "Process")
$jwtSecret = [Environment]::GetEnvironmentVariable("JWT_SECRET_KEY", "Process")

if ([string]::IsNullOrEmpty($openaiKey) -or $openaiKey -eq "sk-your-openai-api-key-here") {
    Write-Host "ERROR: OPENAI_API_KEY not configured in .env" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($pineconeKey) -or $pineconeKey -eq "your-pinecone-api-key-here") {
    Write-Host "ERROR: PINECONE_API_KEY not configured in .env" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($jwtSecret) -or $jwtSecret -eq "CHANGE_THIS_TO_A_STRONG_RANDOM_KEY") {
    Write-Host "ERROR: JWT_SECRET_KEY not configured in .env" -ForegroundColor Red
    Write-Host "Generate one with: python -c `"import secrets; print(secrets.token_urlsafe(64))`""
    exit 1
}

Write-Host "[OK] Environment variables validated" -ForegroundColor Green

# Get port settings
$apiPort = [Environment]::GetEnvironmentVariable("API_PORT", "Process")
if ([string]::IsNullOrEmpty($apiPort)) { $apiPort = "8000" }

$frontendPort = [Environment]::GetEnvironmentVariable("FRONTEND_PORT", "Process")
if ([string]::IsNullOrEmpty($frontendPort)) { $frontendPort = "3000" }

# Check for virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Checking dependencies..."
pip install -q -r requirements.txt

# Create uploads directory
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
}

Write-Host ""
Write-Host "=============================================="
Write-Host "  Starting Services"
Write-Host "=============================================="

# Start API server in new window
Write-Host "Starting API server on port $apiPort..."
$apiProcess = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; uvicorn radio_assistance.mainapp.process_dicom_endpoint:app --host 0.0.0.0 --port $apiPort" -PassThru

# Wait for API to start
Start-Sleep -Seconds 3

# Start frontend server in new window
Write-Host "Starting frontend server on port $frontendPort..."
$frontendProcess = Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd frontend; python -m http.server $frontendPort" -PassThru

Write-Host ""
Write-Host "=============================================="
Write-Host "  Services Started Successfully!" -ForegroundColor Green
Write-Host "=============================================="
Write-Host ""
Write-Host "  Frontend: http://localhost:$frontendPort" -ForegroundColor Cyan
Write-Host "  API:      http://localhost:$apiPort" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:$apiPort/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Default login credentials:"
Write-Host "  Admin:       admin / admin123"
Write-Host "  Radiologist: radiologist / rad123"
Write-Host "  User:        user / user123"
Write-Host ""
Write-Host "Press any key to stop all services..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup
Write-Host "Stopping services..."
Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
Write-Host "Services stopped."



