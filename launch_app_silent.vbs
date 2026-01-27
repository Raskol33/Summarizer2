Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to the script directory and run the command
objShell.CurrentDirectory = strScriptPath
objShell.Run "python -m streamlit run app_final.py", 0, False

Set objShell = Nothing
Set objFSO = Nothing
