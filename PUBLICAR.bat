@echo off
cd /d "%~dp0"
echo ===============================================
echo   Publicando alteracoes da Calculadora Optica
echo ===============================================
echo.
echo [1/3] Sincronizando com o GitHub...
git pull --rebase origin main
if errorlevel 1 goto erro
echo.
echo [2/3] Registrando e versionando as alteracoes...
git add -A
git diff --cached --quiet && goto sopush
git commit -m "Atualiza planilha de SFPs (%date% %time%)"
:sopush
echo.
echo [3/3] Enviando para o GitHub...
git push origin main
if errorlevel 1 goto erro
echo.
echo ===============================================
echo   Publicado com sucesso!
echo   O app atualiza sozinho em 1-3 min.
echo   Se nao atualizar: Manage app - Reboot app.
echo ===============================================
echo.
pause
exit /b 0
:erro
echo.
echo *** Ocorreu um erro ao sincronizar/enviar. ***
echo *** Feche a planilha no LibreOffice e tente de novo, ***
echo *** ou peca ajuda ao suporte.                        ***
echo.
pause
exit /b 1
