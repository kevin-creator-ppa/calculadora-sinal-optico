@echo off
cd /d "%~dp0"
echo ===============================================
echo   Publicando alteracoes da Calculadora Optica
echo ===============================================
echo.
echo [1/4] Sincronizando com o GitHub...
git pull --rebase origin main
if errorlevel 1 goto erro
echo.
echo [2/4] Validando a planilha gbics.csv...
python validar_gbics.py
if errorlevel 1 goto invalido
echo.
echo [3/4] Registrando e versionando as alteracoes...
git add -A
git diff --cached --quiet && goto sopush
git commit -m "Atualiza planilha de SFPs (%date% %time%)"
:sopush
echo.
echo [4/4] Enviando para o GitHub...
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
:invalido
echo.
echo ===============================================
echo   PUBLICACAO CANCELADA - a planilha tem erros.
echo   Veja a lista acima, corrija no LibreOffice,
echo   salve e rode o PUBLICAR.bat de novo.
echo   (Nada foi enviado ao GitHub.)
echo ===============================================
echo.
pause
exit /b 1
:erro
echo.
echo *** Ocorreu um erro ao sincronizar/enviar. ***
echo *** Feche a planilha no LibreOffice e tente de novo, ***
echo *** ou peca ajuda ao suporte.                        ***
echo.
pause
exit /b 1
