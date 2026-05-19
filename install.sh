#!/usr/bin/env bash
# ─── TOM V2.0 — Installateur macOS / Linux ───
# Usage:
#   curl -sSL https://raw.githubusercontent.com/theturbos/tom-job-hunter/main/install.sh | bash
#   ou localement :  bash install.sh
set -euo pipefail

# Couleurs (compatibles POSIX)
if [ -t 1 ]; then
  G='\033[0;32m'; Y='\033[1;33m'; C='\033[0;36m'; R='\033[0;31m'; NC='\033[0m'
else
  G=''; Y=''; C=''; R=''; NC=''
fi

echo -e "${C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${C}  🔍 TOM V2.0 — Installateur${NC}"
echo -e "${C}  © Matthias Dubois — Tous droits réservés${NC}"
echo -e "${C}  🔗 linkedin.com/in/matthias-dubois${NC}"
echo -e "${C}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── 1. Vérifications ──────────────────────────────────────────
# Réattache stdin au terminal (important pour curl|bash)
exec < /dev/tty

if ! command -v python3 &>/dev/null; then
    echo -e "${R}❌ Python 3 requis.${NC}"
    echo -e "   macOS :  ${Y}brew install python3${NC}"
    echo -e "   Ubuntu : ${Y}sudo apt install python3 python3-venv${NC}"
    exit 1
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>/dev/null)
PYMAJ=${PYVER%%.*}
if [ "$PYMAJ" -lt 3 ]; then
    echo -e "${R}❌ Python 3.6+ requis. Vous avez $PYVER${NC}"
    exit 1
fi
echo -e "${G}✅ Python $PYVER${NC}"

if ! command -v git &>/dev/null; then
    echo -e "${Y}⚠️  git non trouvé — on continuera sans clone${NC}"
    HAS_GIT=0
else
    echo -e "${G}✅ Git détecté${NC}"
    HAS_GIT=1
fi

# ── 2. Répertoire d'installation ──────────────────────────────
INSTALL_DIR="${TOM_INSTALL_DIR:-$HOME/.tom-job-hunter}"
REPO="${TOM_REPO:-https://github.com/theturbos/tom-job-hunter.git}"

if [ -f "bot.py" ]; then
    # On est déjà dans le dossier source → copie locale
    echo -e "📂 Copie locale vers ${C}$INSTALL_DIR${NC}..."
    mkdir -p "$INSTALL_DIR"
    cp -r bot.py src/ data/ templates/ lettres/ requirements.txt config.example.yaml \
          install.sh install.bat .gitignore README.md "$INSTALL_DIR/" 2>/dev/null || true
elif [ $HAS_GIT -eq 1 ]; then
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo -e "${Y}📂 Déjà installé dans $INSTALL_DIR — mise à jour...${NC}"
        cd "$INSTALL_DIR" && git pull --ff-only 2>/dev/null || true
    else
        echo -e "📂 Clonage dans ${C}$INSTALL_DIR${NC}..."
        if git clone --depth 1 "$REPO" "$INSTALL_DIR" 2>/dev/null; then
            echo -e "${G}✅ Clone réussi${NC}"
        else
            echo -e "${Y}⚠️  Clone échoué (repo privé?)"
            echo -e "   Téléchargez le zip : ${C}$REPO${NC}"
            echo -e "   Décompressez et relancez ce script dans le dossier.${NC}"
            exit 1
        fi
            fi
else
    echo -e "${R}❌ Aucune source trouvée.${NC}"
    echo -e "   Placez-vous dans le dossier tom-job-hunter avant de lancer ce script."
    exit 1
fi

cd "$INSTALL_DIR"

# ── 3. Virtualenv ─────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo -e "🐍 Création de l'environnement virtuel..."
    python3 -m venv .venv 2>/dev/null || python3 -c "import venv; venv.create('.venv', with_pip=True)" 2>/dev/null || {
        echo -e "${Y}⚠️  Impossible de créer un virtualenv. Installation en --user.${NC}"
        # Fallback: install en --user dans l'environnement système
        pip3 install --user -q pyyaml python-docx colorama 2>/dev/null || {
            echo -e "${R}❌ Échec de l'installation des dépendances.${NC}"
            echo -e "   Essayez : pip3 install --user pyyaml python-docx colorama"
            exit 1
        }
        echo -e "${G}✅ Dépendances installées en --user${NC}"
        echo ""
        echo -e "${G}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${G}  ✅ TOM V2.0 installé !${NC}"
        echo -e "${G}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "  ${C}Lancement du wizard de configuration...${NC}"
        echo ""
        python3 bot.py
        echo ""
        echo -e "  ${G}🚀 Pour lancer TOM V2.0 :${NC}"
        echo -e "  ${Y}cd $INSTALL_DIR && python3 bot.py${NC}"
        echo ""
        exit 0
    }
fi

source .venv/bin/activate 2>/dev/null || . .venv/bin/activate 2>/dev/null || {
    echo -e "${Y}⚠️  Activation du venv échouée — on continue sans.${NC}"
}

echo -e "📦 Installation des dépendances..."
pip install -q --upgrade pip 2>/dev/null || true
if pip install -q -r requirements.txt 2>/dev/null; then
    echo -e "${G}✅ Dépendances installées${NC}"
else
    echo -e "${Y}⚠️  Certaines dépendances n'ont pas pu être installées.${NC}"
    echo -e "   Essayez manuellement : pip install -r requirements.txt"
fi

echo ""
echo -e "${G}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${G}  ✅ TOM V2.0 installé !${NC}"
echo -e "${G}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ── Raccourci bureau (macOS/Linux) ──
echo -e "📌 Création du raccourci..."

# macOS: crée un .app bundle (double-clic depuis le Finder, supporte icône + Dock)
if [[ "$OSTYPE" == "darwin"* ]]; then
    DESKTOP="$HOME/Desktop"

    # ── Icône .icns (nomenclature officielle Apple) ──
    ICONSET="$INSTALL_DIR/assets/TOM.iconset"
    mkdir -p "$ICONSET"
    # Apple iconutil exige ces noms exacts (1x = nom_sans_@, 2x = nom_avec_@2x)
    sips -z 16 16   "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_16x16.png" 2>/dev/null
    sips -z 32 32   "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_16x16@2x.png" 2>/dev/null
    sips -z 32 32   "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_32x32.png" 2>/dev/null
    sips -z 64 64   "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_32x32@2x.png" 2>/dev/null
    sips -z 128 128 "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_128x128.png" 2>/dev/null
    sips -z 256 256 "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_128x128@2x.png" 2>/dev/null
    sips -z 256 256 "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_256x256.png" 2>/dev/null
    sips -z 512 512 "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_256x256@2x.png" 2>/dev/null
    sips -z 512 512 "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_512x512.png" 2>/dev/null
    sips -z 1024 1024 "$INSTALL_DIR/assets/icon.png" --out "$ICONSET/icon_512x512@2x.png" 2>/dev/null
    iconutil -c icns "$ICONSET" -o "$INSTALL_DIR/assets/TOM.icns" 2>/dev/null && \
        echo -e "${G}✅ Icône .icns créée${NC}" || \
        echo -e "${Y}⚠️  Icône .icns non créée (sips/iconutil indisponible)${NC}"
    rm -rf "$ICONSET"

    # ── Création d'un .app bundle minimal (seule solution pour icône + Dock sur macOS) ──
    APP_NAME="TOM Job Hunter"
    APP_DIR="$DESKTOP/$APP_NAME.app"
    mkdir -p "$APP_DIR/Contents/MacOS"
    mkdir -p "$APP_DIR/Contents/Resources"

    # Info.plist minimal
    cat > "$APP_DIR/Contents/Info.plist" << TOMPLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>TOM Job Hunter</string>
    <key>CFBundleIconFile</key>
    <string>TOM</string>
    <key>CFBundleIdentifier</key>
    <string>ai.openclaw.tom-job-hunter</string>
    <key>CFBundleName</key>
    <string>TOM Job Hunter</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
</dict>
</plist>
TOMPLIST

    # Script exécutable (lance TOM dans une nouvelle fenêtre Terminal)
    cat > "$APP_DIR/Contents/MacOS/TOM Job Hunter" << 'TOMEXEC'
#!/bin/bash
# Ouvre TOM dans une nouvelle fenêtre Terminal (reste ouverte après le run)
CMD="cd \"$HOME/.tom-job-hunter\" && [ -f \".venv/bin/activate\" ] && source .venv/bin/activate; python3 bot.py; echo ''; echo 'Appuyez sur Entrée pour fermer...'; read"
osascript -e "tell application \"Terminal\"" -e "activate" -e "do script \"$CMD\""
TOMEXEC
    chmod +x "$APP_DIR/Contents/MacOS/TOM Job Hunter"

    # Copier l'icône
    cp "$INSTALL_DIR/assets/TOM.icns" "$APP_DIR/Contents/Resources/TOM.icns" 2>/dev/null

    # Rafraîchir le cache icônes du Finder
    touch "$APP_DIR" 2>/dev/null
    # Notifier le Finder pour qu'il recharge l'icône du .app
    osascript -e "tell application \"Finder\" to update item (POSIX file \"$APP_DIR\" as alias)" 2>/dev/null || true

    echo -e "${G}✅ Raccourci Bureau créé : TOM Job Hunter.app${NC}"

# Linux: crée un .desktop (double-clic depuis le bureau)
elif [[ "$OSTYPE" == "linux"* ]]; then
    DESKTOP="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
    SHORTCUT="$DESKTOP/TOM-Job-Hunter.desktop"
    cat > "$SHORTCUT" << TOMDESKTOP
[Desktop Entry]
Type=Application
Name=TOM Job Hunter
Comment=Agent de recherche d'emploi
Exec=bash -c 'cd $INSTALL_DIR && source .venv/bin/activate && python3 bot.py; read -p "Appuyez sur Entrée..."'
Icon=terminal
Terminal=true
Categories=Office;
TOMDESKTOP
    chmod +x "$SHORTCUT"
    echo -e "${G}✅ Raccourci créé sur le Bureau : TOM Job Hunter${NC}"
fi

echo ""
echo -e "  ${C}Lancement du wizard de configuration...${NC}"
echo ""

python3 bot.py

echo ""
echo -e "  🚀 Pour lancer TOM V2.0 :"
echo -e "     Double-clic sur ${Y}TOM Job Hunter.app${NC} sur le Bureau"
echo -e "     OU : ${Y}cd $INSTALL_DIR && source .venv/bin/activate && python3 bot.py${NC}"
echo ""
