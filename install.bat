@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ==================================================
echo   TOM V2.0 - Installateur Windows
echo   (c) Matthias Dubois - Tous droits reserves
echo ==================================================
echo.

REM 1. Python
python --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERREUR] Python non trouve.
    echo.
    echo   Installez Python 3.10+ depuis :
    echo   https://www.python.org/downloads/
    echo   IMPORTANT : cochez "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYVER=%%V
echo [OK] Python %PYVER%

REM 2. Git optionnel
git --version >nul 2>&1
if %errorlevel% EQU 0 (
    echo [OK] Git detecte
    set HAS_GIT=1
) else (
    echo [INFO] Git non trouve - installation locale
    set HAS_GIT=0
)

REM 3. Repertoire d'installation
set "INSTALL_DIR=%USERPROFILE%\.tom-job-hunter"
set "REPO=https://github.com/theturbos/tom-job-hunter.git"

if exist "bot.py" (
    echo [INFO] Source locale detectee - copie vers %INSTALL_DIR%
    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    xcopy /E /I /Y /Q bot.py "%INSTALL_DIR%" >nul 2>&1
    if exist "src" xcopy /E /I /Y /Q src "%INSTALL_DIR%\src" >nul 2>&1
    if exist "data" xcopy /E /I /Y /Q data "%INSTALL_DIR%\data" >nul 2>&1
    if exist "templates" xcopy /E /I /Y /Q templates "%INSTALL_DIR%\templates" >nul 2>&1
    if exist "lettres" xcopy /E /I /Y /Q lettres "%INSTALL_DIR%\lettres" >nul 2>&1
    if exist "requirements.txt" copy /Y "requirements.txt" "%INSTALL_DIR%" >nul 2>&1
    if exist "config.example.yaml" copy /Y "config.example.yaml" "%INSTALL_DIR%" >nul 2>&1
    if exist ".gitignore" copy /Y ".gitignore" "%INSTALL_DIR%" >nul 2>&1
    if exist "README.md" copy /Y "README.md" "%INSTALL_DIR%" >nul 2>&1
    if exist "install.bat" copy /Y "install.bat" "%INSTALL_DIR%" >nul 2>&1
    if exist "install.sh" copy /Y "install.sh" "%INSTALL_DIR%" >nul 2>&1
) else if "%HAS_GIT%"=="1" (
    if exist "%INSTALL_DIR%\.git" (
        echo [INFO] Deja installe - mise a jour...
        cd /d "%INSTALL_DIR%"
        git pull --ff-only 2>nul
    ) else (
        echo [INFO] Clonage depuis %REPO%...
        git clone --depth 1 "%REPO%" "%INSTALL_DIR%" 2>nul
        if %errorlevel% NEQ 0 (
            echo [ERREUR] Clone echoue.
            echo   Verifiez votre connexion internet.
            echo   Ou telechargez le zip depuis :
            echo   %REPO%
            pause
            exit /b 1
        )
    )
    ) else (
    echo [ERREUR] Aucune source tom-job-hunter trouvee.
    echo   Placez-vous dans le dossier tom-job-hunter avant de lancer ce script.
    echo   Ou mettez bot.py et le dossier src/ dans le meme dossier.
    pause
    exit /b 1
)

cd /d "%INSTALL_DIR%"

REM 4. Virtualenv
if not exist ".venv" (
    echo [INFO] Creation de l'environnement Python...
    python -m venv .venv 2>nul
    if %errorlevel% NEQ 0 (
        echo [WARN] Impossible de creer le virtualenv.
        echo        Installation en --user...
        python -m pip install --user -q pyyaml python-docx colorama 2>nul
        if %errorlevel% NEQ 0 (
            echo [ERREUR] Echec des dependances.
            pause
            exit /b 1
        )
        echo [OK] Dependances installees en --user
        goto :skip_venv
    )
)

call .venv\Scripts\activate.bat 2>nul
if %errorlevel% NEQ 0 goto :skip_venv

echo [INFO] Installation des dependances...
python -m pip install -q --upgrade pip 2>nul
python -m pip install -q -r requirements.txt 2>nul
if %errorlevel% NEQ 0 (
    echo [WARN] Certaines dependances indisponibles. Installation partielle.
)

REM colorama est critique pour Windows (active les couleurs ANSI)
python -m pip install -q colorama 2>nul
echo [OK] colorama installe pour les couleurs Windows
goto :wizard

:skip_venv
echo [INFO] Suite sans virtualenv...

:wizard

REM 5. Wizard
echo.
echo ==================================================
echo   Installation terminee !
echo ==================================================
echo.
echo   Lancement du wizard de configuration...
echo.

python bot.py setup

echo.
echo   Pour lancer TOM V2.0 :
echo   cd %INSTALL_DIR%
echo   .venv\Scripts\activate
echo   python bot.py
echo.
REM Pause seulement en mode interactif (double-clic)
if "%TOM_SILENT%"=="" pause
