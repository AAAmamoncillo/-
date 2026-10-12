$backupRoot = Split-Path -Parent $PSScriptRoot
$backupPython = 'C:/Users/ZhuanZ（无密码）/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$backupScript = Join-Path $backupRoot 'work/sync_github.py'
$backupPidPath = Join-Path $backupRoot 'work/sync-watcher.pid'
if (Test-Path -LiteralPath $backupPidPath) {
    $backupExistingPid = Get-Content -LiteralPath $backupPidPath
    $backupExisting = Get-CimInstance Win32_Process -Filter "ProcessId = $backupExistingPid" -ErrorAction SilentlyContinue
    if ($backupExisting -and $backupExisting.CommandLine.Contains($backupScript)) {
        Write-Output 'GitHub 备份已在运行。'
        exit
    }
}
$backupProcess = Start-Process -FilePath $backupPython -ArgumentList @(('"' + $backupScript + '"'),'--watch') -WorkingDirectory $backupRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $backupRoot 'work/sync-watcher.out.log') -RedirectStandardError (Join-Path $backupRoot 'work/sync-watcher.err.log') -PassThru
Set-Content -LiteralPath $backupPidPath -Value $backupProcess.Id
Write-Output 'GitHub 自动备份已启动。每15秒检查聊天及文档变化，失败会重试。'
