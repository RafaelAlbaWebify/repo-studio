@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -B "%~dp0launcher.py" %*
) else (
  python -B "%~dp0launcher.py" %*
)
exit /b %errorlevel%
