pyinstaller --onefile --windowed --icon=Icons/coh.ico COHOpponentBot.py
IF EXIST dist\COHOpponentBot.rar DEL /F dist\COHOpponentBot.rar
rar a -ep dist\COHOpponentBot dist\COHOpponentBot.exe dist\Instructions.txt overlay.html Style\OverlayStyle.css
rar a -r dist\COHOpponentBot OverlayImages\*.png 
del dist\COHOpponentBot.exe
pause