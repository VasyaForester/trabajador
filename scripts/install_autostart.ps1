# Install regular mailing: Startup shortcut + start bot now (no admin).
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Cmd = Join-Path $Root "scripts\start_bot.cmd"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) { throw "Missing venv python: $Python" }
if (-not (Test-Path $Cmd)) { throw "Missing start_bot.cmd: $Cmd" }

# Stop existing bots (parent+child uv shim ok to kill by commandline)
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and $_.CommandLine -match 'run_bot\.py' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2

$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "TrabajadorTelegramBot.lnk"
$w = New-Object -ComObject WScript.Shell
$lnk = $w.CreateShortcut($lnkPath)
$lnk.TargetPath = $Cmd
$lnk.WorkingDirectory = $Root
$lnk.WindowStyle = 7
$lnk.Description = "trabajador Telegram bot (tasks 09:00, jobs 15:00, motivation Sat 11:00 MSK)"
$lnk.Save()
Write-Host "Startup shortcut created: $lnkPath"

Start-Process -FilePath $Python -ArgumentList "run_bot.py" -WorkingDirectory $Root -WindowStyle Hidden
Start-Sleep -Seconds 5
$procs = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'run_bot\.py' })
Write-Host "Bot process trees:" $procs.Count "(venv shim + uv child = normal)"
$procs | ForEach-Object { Write-Host " PID $($_.ProcessId)" }
Write-Host "Done. Check Telegram for online + catch-up messages."
