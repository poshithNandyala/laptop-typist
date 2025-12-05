Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Kill existing processes on ports 5000 and 8000
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /PID %a /F", 0, True
WshShell.Run "cmd /c for /f ""tokens=5"" %a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %a /F", 0, True

' Start helper server silently
WshShell.Run "pythonw """ & scriptDir & "\helper\typist_server.py""", 0, False

' Wait 1 second
WScript.Sleep 1000

' Start web UI server silently
WshShell.Run "pythonw """ & scriptDir & "\web-ui\server.py""", 0, False
