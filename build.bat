pyinstaller --clean --onefile --windowed --icon=Icons/coh.ico COHOpponentBot.py
IF EXIST dist\COHOpponentBot.zip DEL /F dist\COHOpponentBot.zip
winrar a -ep -afzip dist\COHOpponentBot dist\COHOpponentBot.exe overlay.html 
winrar a -r -afzip dist\COHOpponentBot OverlayImages\*.png Styles\OverlayStyle.css Styles\AlternateOverlayStyle1.css
del dist\COHOpponentBot.exe
pause 