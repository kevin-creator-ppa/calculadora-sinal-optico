@echo off
cd /d "%~dp0"
cls

echo.
echo ================================================================
echo   CALCULADORA DE SINAL OPTICO - Instalador
echo ================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo.
    echo Baixe em: https://www.python.org/downloads/
    echo Marque "Add Python to PATH" durante a instalacao
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.
echo Instalando pacotes necessarios...
echo.

REM Instalar cada pacote
pip install streamlit
pip install pandas
pip install plotly
pip install reportlab

echo.
echo ================================================================
echo   Instalacao concluida!
echo ================================================================
echo.
echo Abrindo aplicacao...
echo.

REM Executar aplicacao
echo Iniciando aplicacao com Python...
python -m streamlit run app.py

pause
