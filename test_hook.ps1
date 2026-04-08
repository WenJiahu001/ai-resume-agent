[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
$n = new-object system.windows.forms.notifyicon
$n.icon = [System.Drawing.SystemIcons]::Information
$n.visible = $true
$n.showballoontip(3000, 'Claude Code', 'Test Notification', [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Seconds 3
$n.Dispose()
