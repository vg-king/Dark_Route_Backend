@echo off
REM Quick server start script

echo Starting Livestock Health API Server...
call myenv\Scripts\activate.bat
python server_enhanced.py
pause
