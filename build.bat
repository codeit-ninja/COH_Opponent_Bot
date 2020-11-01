pyinstaller --onefile --debug=all --icon=coh.ico COHOpponentBot.py
IF EXIST dist\COHOpponentBot.rar DEL /F dist\COHOpponentBot.rar
rar a -ep dist\COHOpponentBot dist\COHOpponentBot.exe dist\Instructions.txt overlay.html overlaystyle.css
rar a -r dist\COHOpponentBot OverlayImages\*.png 
REM del dist\COHOpponentBot.exe
pause