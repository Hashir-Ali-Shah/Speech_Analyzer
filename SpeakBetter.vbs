Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\ML\speech-to-text"
WshShell.Run """" & "C:\Program Files\Python311\python.exe" & """ desktop.py", 0, False
