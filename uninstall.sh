#!/usr/bin/env bash
# ─── TOM V2.0 — Desinstallateur macOS / Linux ───
set -euo pipefail

INSTALL_DIR="$HOME/.tom-job-hunter"

echo "=================================================="
echo "  TOM V2.0 - Désinstallateur"
echo "=================================================="
echo ""
echo "  Ce script va supprimer :"
echo "    - $INSTALL_DIR"
echo "    - Raccourcis Bureau"
echo ""
echo "  ⚠️  Vos données (config, offres, lettres) seront SUPPRIMÉES."
echo ""
read -p "  Confirmer ? (tapez OUI en majuscules) : " CONFIRM

if [ "$CONFIRM" != "OUI" ]; then
    echo "  Annulé."
    exit 0
fi

echo ""
echo "  Suppression du dossier .tom-job-hunter..."
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "  ✅ Dossier supprimé"
else
    echo "  ⚠️  Dossier introuvable"
fi

echo "  Suppression des raccourcis Bureau..."
rm -f "$HOME/Desktop/TOM Job Hunter.command" 2>/dev/null
rm -f "$HOME/Desktop/TOM-Job-Hunter.desktop" 2>/dev/null
echo "  ✅ Raccourcis supprimés"

echo ""
echo "  ✅ Désinstallation terminée."
echo ""
