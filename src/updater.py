"""
updater.py — Mise à jour auto de TOM V2.0
Stratégie : git pull (si repo) ou download zip (fallback)
Ne touche JAMAIS au dossier data/ ni aux lettres/
"""
from src.colors import green as _green, red as _red, yellow as _yellow
from src.colors import cyan as _cyan, bold as _bold, dim as _dim

import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path

VERSION = "2.0"
_BASE = Path(__file__).resolve().parent.parent  # dossier tom-job-hunter


def _is_git_repo():
    """Vérifie si on est dans un clone git."""
    return (_BASE / ".git").is_dir()


def _current_version():
    """Lit la version actuelle depuis VERSION (fichier dédié) ou bot.py."""
    import re
    # 1) D'abord le fichier VERSION
    ver_file = _BASE / "VERSION"
    if ver_file.exists():
        return ver_file.read_text(encoding="utf-8").strip()
    # 2) Fallback : extrait depuis bot.py
    bot_py = _BASE / "bot.py"
    if not bot_py.exists():
        return None
    text = bot_py.read_text(encoding="utf-8")
    m = re.search(r'VERSION\s*=\s*"([^"]+)"', text)
    return m.group(1) if m else None


def _stash_and_pull():
    """git stash → git pull → git stash pop. Retourne (success, message)."""
    try:
        # Sauvegarde les modifs locales
        subprocess.run(
            ["git", "stash", "push", "--include-untracked", "-m", "TOM auto-stash before update"],
            cwd=str(_BASE), capture_output=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        # Pull
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=str(_BASE), capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            # Restaurer le stash
            subprocess.run(["git", "stash", "pop"], cwd=str(_BASE), capture_output=True, timeout=10,
                           encoding="utf-8", errors="replace")
            return False, f"git pull échoué: {result.stderr.strip()[:200]}"

        # Restaurer le stash
        pop = subprocess.run(
            ["git", "stash", "pop"],
            cwd=str(_BASE), capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        if pop.returncode != 0 and "No stash" not in pop.stderr:
            # Conflit — le stash est toujours là, on prévient
            return True, "Mis à jour, mais conflit avec vos modifications locales. Faites 'git stash list'."

        return True, "Mis à jour avec succès."
    except FileNotFoundError:
        return False, "git non trouvé."
    except subprocess.TimeoutExpired:
        return False, "Timeout — vérifiez votre connexion."
    except Exception as e:
        return False, str(e)[:200]


def _download_and_extract():
    """Fallback sans git : télécharge le zip et extrait tout SAUF data/ et lettres/."""
    import urllib.request
    import zipfile
    import io

    repo_url = os.environ.get(
        "TOM_REPO",
        "https://github.com/theturbos/tom-job-hunter/archive/refs/heads/main.zip"
    )

    print(f"  {_dim('Téléchargement depuis GitHub...')}")
    try:
        req = urllib.request.Request(repo_url, headers={"User-Agent": "TOM-Updater/2.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            zip_data = io.BytesIO(resp.read())
    except Exception as e:
        return False, f"Téléchargement échoué: {e}"

    # Extrait dans un dossier temporaire
    tmpdir = Path(tempfile.mkdtemp(prefix="tom_update_"))
    try:
        with zipfile.ZipFile(zip_data, 'r') as zf:
            zf.extractall(tmpdir)
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return False, f"Extraction échouée: {e}"

    src_dir = extracted_dirs[0]  # dossier tom-job-hunter-main dans le zip
    extracted_dirs = [d for d in tmpdir.iterdir() if d.is_dir()]
    if not extracted_dirs:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return False, "Archive vide ou mal formée."
    src_dir = extracted_dirs[0]

    # Copie tout SAUF data/ et lettres/
    protected = {"data", "lettres", ".venv", "venv", "__pycache__"}
    updated = 0
    skipped = 0
    for item in src_dir.iterdir():
        if item.name in protected:
            skipped += 1
            continue
        dest = _BASE / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
        updated += 1

    shutil.rmtree(tmpdir, ignore_errors=True)
    return True, f"{updated} fichiers mis à jour, {skipped} dossiers protégés (data/, lettres/)"


def check_for_updates():
    """Vérifie si une mise à jour est disponible. Retourne (update_dispo, version_distante)."""
    if not _is_git_repo():
        return None, None  # Pas de git = impossible de vérifier sans télécharger

    try:
        # Fetch silencieux
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=str(_BASE), capture_output=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        # Compare
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/main"],
            cwd=str(_BASE), capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        )
        behind = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        if behind > 0:
            # Récupère la version distante
            show = subprocess.run(
                ["git", "show", "origin/main:bot.py"],
                cwd=str(_BASE), capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace"
            )
            import re
            m = re.search(r'VERSION\s*=\s*"([^"]+)"', show.stdout)
            remote_version = m.group(1) if m else "?"
            return True, remote_version
        return False, None
    except Exception:
        return None, None


def run_update(force=False):
    """
    Lance la mise à jour. Protège data/ et lettres/.
    Retourne (success, message).
    """
    current = _current_version()
    print(f"\n  {_bold('🔄 Mise à jour TOM V2.0')}")
    print(f"  Version actuelle : {_cyan(current or '?')}")
    print(f"  Dossier protégé : {_green('data/')} {_green('lettres/')}")
    print()

    # Backup de sécurité des données
    data_dir = _BASE / "data"
    backup_dir = _BASE / "data_backup"
    if data_dir.exists():
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)
        shutil.copytree(data_dir, backup_dir)
        print(f"  {_dim('Backup data/ → data_backup/')}")

    success = False
    message = ""

    if _is_git_repo():
        print(f"  {_dim('Méthode : git pull')}")
        # Sauvegarde la version du fichier de config si l'utilisateur l'a modifié
        # (le .gitignore protège déjà data/ donc git pull ne le touche pas)
        success, message = _stash_and_pull()
    else:
        print(f"  {_dim('Méthode : téléchargement zip')}")
        success, message = _download_and_extract()

    # Vérifie l'intégrité des données
    if data_dir.exists() and backup_dir.exists():
        # Si data/ a été effacé par erreur, restaurer
        if not (data_dir / "config.yaml").exists() and (backup_dir / "config.yaml").exists():
            print(f"  {_yellow('⚠️  data/ endommagé — restauration du backup.')}")
            shutil.rmtree(data_dir, ignore_errors=True)
            shutil.copytree(backup_dir, data_dir)
        shutil.rmtree(backup_dir, ignore_errors=True)

    new_version = _current_version()
    if success:
        print(f"\n  {_green('✅ ' + message)}")
        if new_version and new_version != current:
            print(f"  {_bold(f'Version: {current} → {_green(new_version)}')}")
    else:
        print(f"\n  {_red('❌ ' + message)}")
        print(f"  {_dim('Vos données sont intactes.')}")

    return success, message
