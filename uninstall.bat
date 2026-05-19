@echo off
chcp 65001 >nul 2>&1
echo ==================================================
echo   TOM V2.0 - Desinstallateur Windows
echo ==================================================
echo.
echo   Ce script va supprimer :
echo     - %USERPROFILE%\.tom-job-hunter
echo     - Raccourci Bureau TOM Job Hunter
echo.
echo   ⚠️  Vos données (config, offres, lettres) seront SUPPRIMÉES.
echo.
set /p CONFIRM="  Confirmer ? (tapez OUI en majuscules) : "

if not "%CONFIRM%"=="OUI" (
    echo   Annulé.
    pause
    exit /b 0
)

echo.
echo   Suppression du dossier .tom-job-hunter...
if exist "%USERPROFILE%\.tom-job-hunter" (
    rmdir /s /q "%USERPROFILE%\.tom-job-hunter"
    echo   ✅ Dossier supprimé
) else (
    echo   ⚠️  Dossier introuvable
)

echo   Suppression des raccourcis Bureau...
if exist "%USERPROFILE%\Desktop\TOM Job Hunter.lnk" (
    del /q "%USERPROFILE%\Desktop\TOM Job Hunter.lnk"
    echo   ✅ Raccourci .lnk supprimé
)
if exist "%USERPROFILE%\Desktop\TOM Job Hunter.bat" (
    del /q "%USERPROFILE%\Desktop\TOM Job Hunter.bat"
    echo   ✅ Raccourci .bat supprimé
)
if exist "%USERPROFILE%\Desktop\TOM Job Hunter.vbs" (
    del /q "%USERPROFILE%\Desktop\TOM Job Hunter.vbs"
    echo   ✅ Raccourci .vbs supprimé
)

echo.
echo   ✅ Désinstallation terminée.
echo.
pause
