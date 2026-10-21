$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$template = Join-Path $PSScriptRoot 'resume_demo_input.csv'
$stamp = Get-Date -Format 'yyyyMMddHHmmss'
$input = Join-Path $PSScriptRoot "resume_demo_recording_input_$stamp.csv"
$prefix = "RECORD-$stamp"

$templateRows = @(Import-Csv -LiteralPath $template)
$recordingRows = for ($i = 0; $i -lt $templateRows.Count; $i++) {
    [pscustomobject]@{
        review_id = '{0}-{1:D3}' -f $prefix, ($i + 1)
        review_text = $templateRows[$i].review_text
        review_rating = $templateRows[$i].review_rating
        review_likes = $templateRows[$i].review_likes
        app_version = $templateRows[$i].app_version
        review_timestamp = $templateRows[$i].review_timestamp
    }
}
$recordingRows | Export-Csv -LiteralPath $input -NoTypeInformation -Encoding UTF8

Write-Host "Preflight for a new 30-row synthetic sample: $input" -ForegroundColor Cyan
& $python cost\pilot.py cold --input $input --workers 2 --preflight-only
if ($LASTEXITCODE -ne 0) { throw 'Preflight stopped. No API calls were made.' }

Write-Host ''
Write-Host 'Start Windows screen recording now (Win+Alt+R), then press Enter here to begin.' -ForegroundColor Yellow
[void](Read-Host)

& $python cost\pilot.py cold --input $input --workers 2 --stop-after-enrichments 4 --execute
if ($LASTEXITCODE -ne 0) { throw 'The run did not reach its saved pause. Review the output before resuming.' }

Write-Host ''
Write-Host 'The runner is paused after saving four results. Keep recording this checkpoint, then press Enter to resume.' -ForegroundColor Yellow
[void](Read-Host)

& $python cost\pilot.py cold --input $input --workers 2 --resume --execute
if ($LASTEXITCODE -ne 0) { throw 'Resume did not complete. Keep the recording and review the saved run state.' }

Write-Host ''
Write-Host 'The 30-row synthetic run is complete. Stop recording now (Win+Alt+R).' -ForegroundColor Green
[void](Read-Host 'Press Enter after the recording has stopped')
