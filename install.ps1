# TOM V2.0 - Installateur Windows (PowerShell)
# (c) Matthias Dubois - Tous droits reserves
# Usage: iwr -useb https://raw.githubusercontent.com/theturbos/tom-job-hunter/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host "  TOM V2.0 - Installateur Windows"                   -ForegroundColor Cyan
Write-Host "  (c) Matthias Dubois - Tous droits reserves"        -ForegroundColor Cyan
Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host ""

# ── 1. Python ────────────────────────────────────────────────
try {
    $pyVer = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python not found" }
    Write-Host "[OK] $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Python 3.10+ non trouve." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Installez Python depuis :" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "  IMPORTANT : cochez 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}

# ── 2. Dossier d'installation ───────────────────────────────
$InstallDir = "$env:USERPROFILE\.tom-job-hunter"
$RepoUrl = "https://github.com/theturbos/tom-job-hunter.git"
$ZipUrl = "https://github.com/theturbos/tom-job-hunter/archive/refs/heads/main.zip"

# Si on est deja dans le dossier source -> copie locale
if (Test-Path "bot.py") {
    Write-Host "[INFO] Source locale detectee - copie vers $InstallDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    Copy-Item -Recurse -Force bot.py, src, data, templates, lettres, requirements.txt, config.example.yaml, install.bat, install.sh, .gitignore, README.md, assets -Destination $InstallDir -ErrorAction SilentlyContinue
} else {
    # Essayer git, sinon zip
    $gitOk = $false
    try {
        git --version 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { $gitOk = $true }
    } catch { }

    if ($gitOk) {
        if (Test-Path "$InstallDir\.git") {
            Write-Host "[INFO] Deja installe - mise a jour..." -ForegroundColor Yellow
            Set-Location $InstallDir
            git pull --ff-only 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[WARN] git pull echoue, on continue..." -ForegroundColor Yellow
            }
        } else {
            Write-Host "[INFO] Clonage depuis GitHub..." -ForegroundColor Yellow
            git clone --depth 1 $RepoUrl $InstallDir 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERREUR] Clone echoue. Tentative zip..." -ForegroundColor Yellow
                $gitOk = $false
            } else {
                Write-Host "[OK] Clone termine" -ForegroundColor Green
            }
        }
    }

    if (-not $gitOk) {
        Write-Host "[INFO] Telechargement du zip..." -ForegroundColor Yellow
        $zipPath = "$env:TEMP\tom-job-hunter.zip"
        $extractPath = "$env:TEMP\tom-job-hunter-main"

        try {
            Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath -ErrorAction Stop
            Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP" -Force
            Remove-Item $zipPath -Force

            if (Test-Path $extractPath) {
                New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
                Copy-Item -Recurse -Force "$extractPath\*" -Destination $InstallDir
                Remove-Item -Recurse -Force $extractPath
                Write-Host "[OK] Installation par zip reussie" -ForegroundColor Green
            } else {
                Write-Host "[ERREUR] Extraction echouee." -ForegroundColor Red
                Read-Host "Appuyez sur Entree pour quitter"
                exit 1
            }
        } catch {
            Write-Host "[ERREUR] Telechargement echoue: $_" -ForegroundColor Red
            Write-Host "  Verifiez votre connexion internet." -ForegroundColor Yellow
            Read-Host "Appuyez sur Entree pour quitter"
            exit 1
        }
    }
}

Set-Location $InstallDir

# ── 3. Virtualenv + dependances ─────────────────────────────
if (-not (Test-Path ".venv")) {
    Write-Host "[INFO] Creation de l'environnement Python..." -ForegroundColor Yellow
    python -m venv .venv 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARN] Virtualenv impossible. Installation en --user..." -ForegroundColor Yellow
        python -m pip install --user -q pyyaml python-docx colorama 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERREUR] Echec des dependances." -ForegroundColor Red
            Read-Host "Appuyez sur Entree pour quitter"
            exit 1
        }
        Write-Host "[OK] Dependances installees en --user" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Installation des dependances..." -ForegroundColor Yellow
        .\.venv\Scripts\python.exe -m pip install -q --upgrade pip 2>&1 | Out-Null
        .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt 2>&1 | Out-Null
        .\.venv\Scripts\python.exe -m pip install -q colorama 2>&1 | Out-Null
        Write-Host "[OK] Dependances installees" -ForegroundColor Green
    }
}

# ── 4. Raccourci bureau avec icone ──────────────────────────
Write-Host ""
Write-Host "  Creation du raccourci bureau..." -ForegroundColor Yellow

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = "$Desktop\TOM Job Hunter.lnk"
$LauncherPath = "$InstallDir\tom-launcher.bat"
$IconPath = "$InstallDir\assets\icon.ico"

# Cree le launcher .bat
@"
@echo off
chcp 65001 >nul 2>&1
cd /d "$InstallDir"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
python bot.py
pause
"@ | Out-File -FilePath $LauncherPath -Encoding UTF8

# Supprime anciens raccourcis
Remove-Item "$ShortcutPath" -Force -ErrorAction SilentlyContinue
Remove-Item "$Desktop\TOM Job Hunter.bat" -Force -ErrorAction SilentlyContinue

# Cree le raccourci .lnk
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $LauncherPath
    $Shortcut.WorkingDirectory = $InstallDir
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = $IconPath
    }
    $Shortcut.Save()
    
    if (Test-Path $ShortcutPath) {
        $iconMsg = if (Test-Path $IconPath) { "avec icone personnalisee" } else { "" }
        Write-Host "[OK] Raccourci cree sur le Bureau : TOM Job Hunter $iconMsg" -ForegroundColor Green
    } else {
        throw "Creation echouee"
    }
} catch {
    Write-Host "[WARN] Creation .lnk echouee, fallback .bat" -ForegroundColor Yellow
    Copy-Item $LauncherPath "$Desktop\TOM Job Hunter.bat" -Force
}

# ── 5. Wizard ───────────────────────────────────────────────
Write-Host ""
Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host "  Installation terminee !"                           -ForegroundColor Cyan
Write-Host "=================================================="  -ForegroundColor Cyan
Write-Host ""
Write-Host "  Lancement du wizard de configuration..."            -ForegroundColor Yellow
Write-Host ""

python bot.py

Write-Host ""
Write-Host "  Pour lancer TOM V2.0 :"                            -ForegroundColor Cyan
Write-Host "     Double-clic sur 'TOM Job Hunter' sur le Bureau"  -ForegroundColor Green
Write-Host "     OU : cd $InstallDir ; .\.venv\Scripts\activate ; python bot.py" -ForegroundColor Green
Write-Host ""
Write-Host "  Vos donnees : $InstallDir\data\"                    -ForegroundColor Yellow
Write-Host "     -> config.yaml, offres.md, candidatures.md"        -ForegroundColor Gray
Write-Host "  Vos lettres : $InstallDir\lettres\"                   -ForegroundColor Yellow
Write-Host ""

if (-not $env:TOM_SILENT) {
    Read-Host "Appuyez sur Entree pour fermer"
}
