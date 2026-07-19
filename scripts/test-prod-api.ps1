$ErrorActionPreference = 'Stop'
$body = @{
  number = 1
  performer = 'MC'
  piece = 'Test'
  is_duet = $false
  lang = 'vi'
  gender = 'female'
  mc_script = 'Thân chào test Trân Oanh.'
} | ConvertTo-Json -Compress

Write-Host '==> GET /api/health'
$health = Invoke-RestMethod -Uri 'https://vmc-mariale-api.onrender.com/api/health' -TimeoutSec 60
$health | ConvertTo-Json

Write-Host ''
Write-Host '==> POST /api/mc/live-token'
$resp = Invoke-RestMethod -Method Post `
  -Uri 'https://vmc-mariale-api.onrender.com/api/mc/live-token' `
  -ContentType 'application/json; charset=utf-8' `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
  -TimeoutSec 90

Write-Host ('model: ' + $resp.model)
Write-Host ('token_len: ' + $resp.token.Length)
$prompt = $resp.opening_prompt
Write-Host ('prompt_len: ' + $prompt.Length)
Write-Host ('has_KICH_BAN_BAT_DAU: ' + $prompt.Contains([char]0x0110)) # rough
Write-Host ('contains_100_percent_marker: ' + ($prompt -match '100%'))
Write-Host ('contains_Tran_Oanh: ' + ($prompt -match 'Trân Oanh'))
Write-Host ('contains_old_style_NHIEM_VU: ' + ($prompt -match 'NHIỆM VỤ'))
Write-Host ('contains_gemini_marker: ' + ($prompt -match 'KỊCH BẢN BẮT ĐẦU'))
Write-Host ''
Write-Host '--- opening_prompt preview ---'
Write-Host $prompt.Substring(0, [Math]::Min(600, $prompt.Length))
