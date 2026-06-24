@echo off
cd /d "%~dp0"

echo.
echo Iniciando Calculadora de Sinal Optico...
echo.

python -m streamlit run app.py

pause
