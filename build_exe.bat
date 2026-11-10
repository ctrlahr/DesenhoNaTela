@echo off
setlocal
cd /d "%~dp0"

echo ==^> Instalando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 goto :erro

echo ==^> Gerando icone...
python ferramentas\gerar_icone.py
if errorlevel 1 goto :erro

echo ==^> Gerando executavel...
python -m PyInstaller --noconfirm --clean DesenhoNaTela.spec
if errorlevel 1 goto :erro

echo.
echo Executavel criado em: %~dp0dist\DesenhoNaTela.exe
pause
exit /b 0

:erro
echo.
echo Falha ao gerar o executavel.
pause
exit /b 1
