# Build production bundle for https://hai1975.com/VMC2/
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Out = Join-Path $Root "deploy\upload"
$VmcWeb = Join-Path $Out "VMC2"
$Frontend = Join-Path $Root "frontend"
$EnvProd = Join-Path $Frontend ".env.production"
$EnvVmc2 = Join-Path $Frontend ".env.production.vmc2"
$EnvBackup = Join-Path $Frontend ".env.production.bak"
$IndexHtml = Join-Path $Frontend "index.html"
$IndexBackup = Join-Path $Frontend "index.html.bak"

$ApiBase = "https://vmc2.onrender.com"
$OldApi = "https://vmc-api-u0fk.onrender.com"

Write-Host "==> Building frontend for VMC2 (base /VMC2/, API $ApiBase)..."

if (Test-Path $EnvProd) { Copy-Item $EnvProd $EnvBackup -Force }
if (Test-Path $IndexHtml) { Copy-Item $IndexHtml $IndexBackup -Force }

try {
  Copy-Item $EnvVmc2 $EnvProd -Force
  $html = Get-Content $IndexHtml -Raw -Encoding UTF8
  $html = $html.Replace($OldApi, $ApiBase)
  Set-Content $IndexHtml $html -Encoding UTF8 -NoNewline

  Push-Location $Frontend
  npm run build
  Pop-Location

  Write-Host "==> Preparing deploy/upload/VMC2/ ..."
  if (Test-Path $VmcWeb) { Remove-Item $VmcWeb -Recurse -Force }
  New-Item -ItemType Directory -Path $VmcWeb -Force | Out-Null
  Copy-Item (Join-Path $Frontend "dist\*") $VmcWeb -Recurse -Force
  Copy-Item (Join-Path $Root "deploy\VMC2\.htaccess") $VmcWeb -Force

  Write-Host ""
  Write-Host "Done. Upload folder: deploy/upload/VMC2/"
  Write-Host "  -> cPanel public_html/VMC2/"
  Write-Host "  API: $ApiBase/api/health"
} finally {
  if (Test-Path $EnvBackup) {
    Move-Item $EnvBackup $EnvProd -Force
  }
  if (Test-Path $IndexBackup) {
    Move-Item $IndexBackup $IndexHtml -Force
  }
}
