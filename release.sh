#!/usr/bin/env bash
# release.sh — Pousse les commits + crée un tag semver automatique
# Usage: ./release.sh [patch|minor|major]
#   patch (défaut) : 2.2 → 2.2.0, 2.2.9 → 2.2.10
#   minor : 2.2 → 2.3.0
#   major : 2.2 → 3.0.0
set -euo pipefail

BUMP="${1:-patch}"
TAG_PREFIX="v"

# Récupère le tag le plus récent, ou 2.2 comme base
LATEST=$(git describe --tags --abbrev=0 2>/dev/null || echo "v2.2")
LATEST="${LATEST#v}"  # v2.2.0 → 2.2.0

IFS='.' read -r MAJ MIN PAT <<< "$LATEST"
PAT="${PAT:-0}"

case "$BUMP" in
    major)
        MAJ=$((MAJ + 1)); MIN=0; PAT=0 ;;
    minor)
        MIN=$((MIN + 1)); PAT=0 ;;
    patch)
        PAT=$((PAT + 1)) ;;
    *)
        echo "Usage: $0 [patch|minor|major]"
        exit 1 ;;
esac

NEW_VERSION="${MAJ}.${MIN}.${PAT}"
NEW_TAG="v${NEW_VERSION}"

echo "🏷️  Version actuelle : $LATEST"
echo "🏷️  Nouveau tag     : $NEW_TAG"
echo ""

# Push les commits
git push origin main

# Crée et push le tag
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"
git push origin "$NEW_TAG"

# Met à jour le fichier VERSION
echo "$NEW_VERSION" > VERSION
git add VERSION
git commit -m "chore: bump version to $NEW_VERSION"
git push origin main

echo ""
echo "✅ Release $NEW_TAG publiée !"
