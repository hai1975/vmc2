# Build production bundle for upload to https://hai1975.com/VMC/
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Out = Join-Path $Root "deploy\upload"
$VmcWeb = Join-Path $Out "VMC"

Write-Host "==> Building frontend (base /VMC/)..."
Push-Location (Join-Path $Root "frontend")
npm run build
Pop-Location

Write-Host "==> Preparing deploy/upload/VMC/ (static frontend)..."
if (Test-Path $VmcWeb) { Remove-Item $VmcWeb -Recurse -Force }
New-Item -ItemType Directory -Path $VmcWeb -Force | Out-Null
Copy-Item (Join-Path $Root "frontend\dist\*") $VmcWeb -Recurse -Force
Copy-Item (Join-Path $Root "deploy\VMC\.htaccess") $VmcWeb -Force

Write-Host ""
Write-Host "Done. Upload folder: deploy/upload/"
Write-Host "  VMC/  -> upload to cPanel public_html/VMC/  (static only)"
Write-Host ""
Write-Host "API (Render/Railway):"
Write-Host "  1. Push repo to GitHub, connect Render or Railway"
Write-Host "  2. Deploy using Dockerfile at repo root"
Write-Host "  3. Set env vars from deploy/paas-env.example (GEMINI_API_KEY, CORS_ORIGINS)"
Write-Host "  4. Copy API URL into frontend/.env.production VITE_API_BASE, rebuild, re-upload VMC/"
Write-Host "  5. Test: https://YOUR-API.onrender.com/api/health"
