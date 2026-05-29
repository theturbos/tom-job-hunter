"""
updater.py — Mise a jour auto de TOM V2.0
Strategie : git fetch + reset --hard (resiste aux force push) + fallback ZIP
"""
from src.colors import green as _green, red as _red, yellow as _yellow
from src.colors import cyan as _cyan, bold as _bold, dim as _dim
import os, sys, json, shutil, tempfile, subprocess
from pathlib import Path
_BASE = Path(__file__).resolve().parent.parent

def _is_git_repo():
    return (_BASE / ".git").is_dir()

def _current_version():
    try:
        r = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], capture_output=True, text=True, cwd=str(_BASE), timeout=5)
        tag = r.stdout.strip()
        if tag and r.returncode == 0:
            return tag.lstrip("v")
    except Exception:
        pass
    ver_file = _BASE / "VERSION"
    if ver_file.exists():
        return ver_file.read_text(encoding="utf-8").strip()
    return "?"

def _stash_and_pull():
    try:
        subprocess.run(["git", "stash", "push", "--include-untracked", "-m", "TOM auto-stash"], cwd=str(_BASE), capture_output=True, timeout=15, encoding="utf-8", errors="replace")
        r = subprocess.run(["git", "fetch", "origin", "--tags", "--force"], cwd=str(_BASE), capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            subprocess.run(["git", "stash", "pop"], cwd=str(_BASE), capture_output=True, timeout=10, encoding="utf-8", errors="replace")
            return False, f"git fetch echoue: {r.stderr.strip()[:200]}"
        behind = subprocess.run(["git", "rev-list", "--count", "HEAD..origin/main"], cwd=str(_BASE), capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        ahead = subprocess.run(["git", "rev-list", "--count", "origin/main..HEAD"], cwd=str(_BASE), capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        bn = int(behind.stdout.strip()) if behind.stdout.strip().isdigit() else 0
        an = int(ahead.stdout.strip()) if ahead.stdout.strip().isdigit() else 0
        if bn == 0 and an == 0:
            subprocess.run(["git", "stash", "pop"], cwd=str(_BASE), capture_output=True, timeout=10, encoding="utf-8", errors="replace")
            return True, "Deja a jour."
        r = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=str(_BASE), capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            subprocess.run(["git", "stash", "pop"], cwd=str(_BASE), capture_output=True, timeout=10, encoding="utf-8", errors="replace")
            return False, f"git reset echoue: {r.stderr.strip()[:200]}"
        pop = subprocess.run(["git", "stash", "pop"], cwd=str(_BASE), capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        if pop.returncode != 0 and "No stash" not in pop.stderr:
            return True, "Mis a jour (conflits locaux possibles)."
        return True, "Mis a jour avec succes."
    except FileNotFoundError:
        return False, "git non trouve."
    except subprocess.TimeoutExpired:
        return False, "Timeout."
    except Exception as e:
        return False, str(e)[:200]

def _download_and_extract():
    import urllib.request, zipfile, io
    repo_url = os.environ.get("TOM_REPO", "https://github.com/theturbos/tom-job-hunter/archive/refs/heads/main.zip")
    print(f"  Telechargement depuis GitHub...")
    try:
        req = urllib.request.Request(repo_url, headers={"User-Agent": "TOM-Updater/2.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            zip_data = io.BytesIO(resp.read())
    except Exception as e:
        return False, f"Telechargement echoue: {e}"
    tmpdir = Path(tempfile.mkdtemp(prefix="tom_update_"))
    try:
        with zipfile.ZipFile(zip_data, 'r') as zf:
            zf.extractall(tmpdir)
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return False, f"Extraction echouee: {e}"
    dirs = [d for d in tmpdir.iterdir() if d.is_dir()]
    if not dirs:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return False, "Archive vide."
    src = dirs[0]
    protected = {"data", "lettres", ".venv", "venv", "__pycache__"}
    updated = 0
    for item in src.iterdir():
        if item.name in protected:
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
    return True, f"{updated} fichiers mis a jour."

def check_for_updates():
    if not _is_git_repo():
        return None, None
    try:
        subprocess.run(["git", "fetch", "origin", "--tags"], cwd=str(_BASE), capture_output=True, timeout=15, encoding="utf-8", errors="replace")
        r = subprocess.run(["git", "rev-list", "--count", "HEAD..origin/main"], cwd=str(_BASE), capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
        behind = int(r.stdout.strip()) if r.stdout.strip().isdigit() else 0
        if behind > 0:
            tr = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "origin/main"], cwd=str(_BASE), capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
            rv = tr.stdout.strip().lstrip("v") if tr.returncode == 0 and tr.stdout.strip() else None
            return True, rv
        return False, None
    except Exception:
        return None, None

def run_update(force=False):
    current = _current_version()
    print(f"\n  Mise a jour TOM V2.0")
    print(f"  Version actuelle : {_cyan(current or '?')}")
    print(f"  Dossier protege : data/ lettres/")
    print()
    data_dir = _BASE / "data"
    backup_dir = _BASE / "data_backup"
    if data_dir.exists():
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)
        shutil.copytree(data_dir, backup_dir)
        print(f"  Backup data/ -> data_backup/")
    success = False
    message = ""
    if _is_git_repo():
        print(f"  Methode : git fetch + reset --hard")
        success, message = _stash_and_pull()
        if not success:
            print(f"  Git echoue, tentative via telechargement zip...")
            success, message = _download_and_extract()
    else:
        print(f"  Methode : telechargement zip")
        success, message = _download_and_extract()
    if data_dir.exists() and backup_dir.exists():
        if not (data_dir / "config.yaml").exists() and (backup_dir / "config.yaml").exists():
            print(f"  data/ endommage - restauration backup...")
            shutil.rmtree(data_dir, ignore_errors=True)
            shutil.copytree(backup_dir, data_dir)
        shutil.rmtree(backup_dir, ignore_errors=True)
    new_version = _current_version()
    if success:
        print(f"\n  OK {message}")
        if new_version and new_version != current:
            print(f"  Version: {current} -> {_green(new_version)}")
    else:
        print(f"\n  ECHEC {message}")
        print(f"  Vos donnees sont intactes.")
        print(f"  Reinstallez depuis github.com/theturbos/tom-job-hunter")
    return success, message
