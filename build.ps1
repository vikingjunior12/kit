poetry run pyinstaller kit.py --onefile --collect-all rich
Copy-Item -Path ".\dist\kit.exe" -Destination "C:\Tools\kit.exe" -Force
