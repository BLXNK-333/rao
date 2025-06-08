$WshShell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $WshShell.CreateShortcut("$desktop\RAO.lnk")
$shortcut.TargetPath = "$PWD\run_app.vbs"
$shortcut.IconLocation = "$PWD\rao.ico"
$shortcut.WorkingDirectory = "$PWD"
$shortcut.Save()
