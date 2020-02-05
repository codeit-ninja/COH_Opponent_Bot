pyinstaller --onefile --windowed --icon=coh.ico COHOpponentBot.py
IF EXIST dist\COHOpponentBot.rar DEL /F dist\COHOpponentBot.rar
rar a -ep dist\COHOpponentBot dist\COHOpponentBot.exe dist\Instructions.txt dist\overlay.html dist\overlaystyle.css
pause